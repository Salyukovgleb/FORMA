-- Phase A design DDL. Not an Alembic migration. PostgreSQL 14+ syntax.
CREATE TABLE users (
 id uuid PRIMARY KEY,
 email varchar(254) NOT NULL UNIQUE CHECK (email = lower(btrim(email))),
 password_hash text NOT NULL,
 display_name varchar(100) NOT NULL CHECK (length(display_name)>0),
 is_active boolean NOT NULL DEFAULT true,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE auth_sessions (
 id uuid PRIMARY KEY,
 user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 refresh_token_hash char(64) NOT NULL UNIQUE,
 csrf_token_hash char(64) NOT NULL,
 expires_at timestamptz NOT NULL,
 revoked_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(),
 rotated_at timestamptz NOT NULL DEFAULT now(),
 CHECK (expires_at > created_at)
);
CREATE INDEX auth_sessions_user ON auth_sessions(user_id, expires_at);
CREATE TABLE used_refresh_tokens (
 token_hash char(64) PRIMARY KEY,
 session_id uuid NOT NULL REFERENCES auth_sessions(id) ON DELETE CASCADE,
 expires_at timestamptz NOT NULL
);
CREATE TABLE projects (
 id uuid PRIMARY KEY,
 owner_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 title varchar(200) NOT NULL CHECK (length(btrim(title))>0),
 description varchar(2000) NOT NULL DEFAULT '',
 main_file_id uuid,
 engine text NOT NULL DEFAULT 'xelatex' CHECK (engine IN ('pdflatex','xelatex','lualatex')),
 status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','deleted')),
 revision bigint NOT NULL DEFAULT 1 CHECK (revision>0),
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 deleted_at timestamptz,
 CHECK ((status='deleted') = (deleted_at IS NOT NULL))
);
CREATE INDEX projects_owner ON projects(owner_id, created_at DESC, id DESC);
CREATE TABLE project_members (
 project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
 user_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 role text NOT NULL CHECK (role IN ('editor','viewer')),
 invited_by uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY (project_id,user_id)
);
CREATE INDEX project_members_user ON project_members(user_id, project_id);
CREATE TABLE project_nodes (
 id uuid PRIMARY KEY,
 project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
 parent_id uuid,
 name varchar(255) NOT NULL CHECK (name NOT IN ('','.','..') AND name !~ '[/\\]'),
 node_type text NOT NULL CHECK (node_type IN ('file','folder')),
 logical_path varchar(1024) NOT NULL CHECK (logical_path !~ '^/' AND logical_path !~ '(^|/)\.\.(/|$)'),
 media_type varchar(100),
 revision bigint NOT NULL DEFAULT 1 CHECK (revision>0),
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 deleted_at timestamptz,
 UNIQUE (project_id,id),
 FOREIGN KEY (project_id,parent_id) REFERENCES project_nodes(project_id,id) DEFERRABLE INITIALLY DEFERRED,
 CHECK (parent_id IS DISTINCT FROM id),
 CHECK ((node_type='folder' AND media_type IS NULL) OR (node_type='file' AND media_type IS NOT NULL))
);
CREATE UNIQUE INDEX nodes_path_live ON project_nodes(project_id,logical_path) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX nodes_siblings_live ON project_nodes(project_id,coalesce(parent_id,'00000000-0000-0000-0000-000000000000'::uuid),name) WHERE deleted_at IS NULL;
ALTER TABLE projects ADD CONSTRAINT project_main_same_project FOREIGN KEY (id,main_file_id) REFERENCES project_nodes(project_id,id) DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE file_revisions (
 id uuid PRIMARY KEY,
 node_id uuid NOT NULL REFERENCES project_nodes(id) ON DELETE CASCADE,
 revision bigint NOT NULL CHECK (revision>0),
 content_storage_key uuid NOT NULL UNIQUE,
 content_hash char(64) NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$'),
 size_bytes bigint NOT NULL CHECK (size_bytes>=0 AND size_bytes<=20971520),
 author_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE (node_id,revision)
);
CREATE TABLE project_snapshots (
 id uuid PRIMARY KEY,
 project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
 project_revision bigint NOT NULL CHECK (project_revision>0),
 main_path varchar(1024),
 engine text NOT NULL CHECK (engine IN ('pdflatex','xelatex','lualatex')),
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE snapshot_entries (
 snapshot_id uuid NOT NULL REFERENCES project_snapshots(id) ON DELETE CASCADE,
 logical_path varchar(1024) NOT NULL,
 node_type text NOT NULL CHECK (node_type IN ('file','folder')),
 revision_id uuid REFERENCES file_revisions(id) ON DELETE RESTRICT,
 PRIMARY KEY (snapshot_id,logical_path),
 CHECK ((node_type='file') = (revision_id IS NOT NULL))
);
CREATE TABLE document_jobs (
 id uuid PRIMARY KEY,
 project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
 requested_by uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 job_type text NOT NULL CHECK (job_type IN ('pdf','docx','zip')),
 state text NOT NULL DEFAULT 'queued' CHECK (state IN ('queued','running','retry_wait','succeeded','failed','cancelled')),
 stage text NOT NULL DEFAULT 'waiting' CHECK (stage IN ('waiting','snapshot','processing','publishing','complete')),
 snapshot_id uuid NOT NULL REFERENCES project_snapshots(id) ON DELETE RESTRICT,
 idempotency_key varchar(128) NOT NULL,
 request_hash char(64) NOT NULL,
 attempt integer NOT NULL DEFAULT 0 CHECK (attempt>=0),
 max_attempts integer NOT NULL DEFAULT 3 CHECK (max_attempts BETWEEN 1 AND 3),
 lease_token uuid,
 lease_until timestamptz,
 heartbeat_at timestamptz,
 next_run_at timestamptz NOT NULL DEFAULT now(),
 cancellation_requested boolean NOT NULL DEFAULT false,
 queued_at timestamptz NOT NULL DEFAULT now(),
 started_at timestamptz,
 finished_at timestamptz,
 error_code varchar(80),
 error_message varchar(2000),
 options_json jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(options_json)='object'),
 UNIQUE (project_id,requested_by,idempotency_key),
 CHECK (attempt<=max_attempts),
 CHECK ((state='running') = (lease_token IS NOT NULL AND lease_until IS NOT NULL)),
 CHECK ((state IN ('succeeded','failed','cancelled')) = (finished_at IS NOT NULL))
);
CREATE INDEX jobs_claim ON document_jobs(state, queued_at) WHERE state IN ('queued','retry_wait');
CREATE INDEX jobs_project ON document_jobs(project_id, queued_at DESC,id DESC);
CREATE INDEX jobs_requester ON document_jobs(requested_by,state);
CREATE INDEX jobs_expired ON document_jobs(lease_until) WHERE state='running';
CREATE TABLE job_artifacts (
 id uuid PRIMARY KEY,
 job_id uuid NOT NULL REFERENCES document_jobs(id) ON DELETE CASCADE,
 artifact_type text NOT NULL CHECK (artifact_type IN ('pdf','docx','zip')),
 storage_key uuid NOT NULL UNIQUE,
 filename varchar(255) NOT NULL,
 mime_type varchar(100) NOT NULL,
 size_bytes bigint NOT NULL CHECK (size_bytes>=0 AND size_bytes<=104857600),
 sha256 char(64) NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
 created_at timestamptz NOT NULL DEFAULT now(),
 expires_at timestamptz NOT NULL,
 UNIQUE (job_id,artifact_type),
 CHECK (expires_at>created_at)
);
CREATE TABLE job_log_entries (
 job_id uuid NOT NULL REFERENCES document_jobs(id) ON DELETE CASCADE,
 sequence bigint NOT NULL CHECK (sequence>0),
 level text NOT NULL CHECK (level IN ('info','warning','error')),
 code varchar(80) NOT NULL,
 message varchar(2000) NOT NULL,
 file varchar(1024),
 line integer CHECK (line>0),
 created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY (job_id,sequence)
);
CREATE TABLE audit_events (
 id uuid PRIMARY KEY,
 actor_id uuid REFERENCES users(id) ON DELETE SET NULL,
 project_id uuid REFERENCES projects(id) ON DELETE SET NULL,
 action varchar(100) NOT NULL,
 entity_type varchar(80) NOT NULL,
 entity_id uuid NOT NULL,
 metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata_json)='object'),
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX audit_project ON audit_events(project_id,created_at DESC);
CREATE TABLE rate_limit_buckets (
 scope varchar(80) NOT NULL,
 subject_hash char(64) NOT NULL,
 window_start timestamptz NOT NULL,
 count integer NOT NULL CHECK (count>=0),
 PRIMARY KEY (scope,subject_hash,window_start)
);
-- Cross-row semantic constraints are checked at commit; application locks project first.
CREATE FUNCTION validate_project_tree() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE pid uuid;
BEGIN
 IF TG_TABLE_NAME='projects' THEN pid:=NEW.id; ELSE pid:=NEW.project_id; END IF;
 IF EXISTS (SELECT 1 FROM projects p JOIN project_nodes n ON n.id=p.main_file_id
 WHERE p.id=pid AND (n.deleted_at IS NOT NULL OR n.node_type<>'file' OR n.name !~ '\.tex$')) THEN
 RAISE EXCEPTION 'invalid main file' USING ERRCODE='23514'; END IF;
 IF EXISTS (SELECT 1 FROM project_nodes n LEFT JOIN project_nodes p ON p.id=n.parent_id
 WHERE n.project_id=pid AND n.deleted_at IS NULL AND
 ((n.parent_id IS NULL AND n.logical_path<>n.name) OR
 (n.parent_id IS NOT NULL AND (p.node_type<>'folder' OR p.deleted_at IS NOT NULL OR n.logical_path<>p.logical_path||'/'||n.name)))) THEN
 RAISE EXCEPTION 'invalid tree path or parent' USING ERRCODE='23514'; END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER nodes_semantics AFTER INSERT OR UPDATE ON project_nodes DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_project_tree();
CREATE CONSTRAINT TRIGGER main_semantics AFTER INSERT OR UPDATE ON projects DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_project_tree();
