-- Valid rows for all 14 tables; disposable database only. Transaction preserves deferred FK semantics.
BEGIN;
INSERT INTO users(id,email,password_hash,display_name) VALUES
 ('00000000-0000-4000-8000-000000000001','owner@example.org','fixture-not-a-real-password-hash','Владелец'),
 ('00000000-0000-4000-8000-000000000002','editor@example.org','fixture-not-a-real-password-hash','Редактор');
INSERT INTO auth_sessions(id,user_id,refresh_token_hash,csrf_token_hash,expires_at) VALUES
 ('00000000-0000-4000-8000-000000000003','00000000-0000-4000-8000-000000000001',repeat('a',64),repeat('b',64),now()+interval '30 days');
INSERT INTO used_refresh_tokens VALUES(repeat('c',64),'00000000-0000-4000-8000-000000000003',now()+interval '30 days');
INSERT INTO projects(id,owner_id,title) VALUES
 ('00000000-0000-4000-8000-000000000004','00000000-0000-4000-8000-000000000001','Статья');
INSERT INTO project_members(project_id,user_id,role,invited_by) VALUES
 ('00000000-0000-4000-8000-000000000004','00000000-0000-4000-8000-000000000002','editor','00000000-0000-4000-8000-000000000001');
INSERT INTO project_nodes(id,project_id,name,node_type,logical_path,media_type) VALUES
 ('00000000-0000-4000-8000-000000000005','00000000-0000-4000-8000-000000000004','main.tex','file','main.tex','text/plain');
UPDATE projects SET main_file_id='00000000-0000-4000-8000-000000000005' WHERE id='00000000-0000-4000-8000-000000000004';
INSERT INTO file_revisions(id,node_id,revision,content_storage_key,content_hash,size_bytes,author_id) VALUES
 ('00000000-0000-4000-8000-000000000006','00000000-0000-4000-8000-000000000005',1,'00000000-0000-4000-8000-000000000007',repeat('d',64),10,'00000000-0000-4000-8000-000000000001');
INSERT INTO project_snapshots(id,project_id,project_revision,main_path,engine) VALUES
 ('00000000-0000-4000-8000-000000000008','00000000-0000-4000-8000-000000000004',1,'main.tex','xelatex');
INSERT INTO snapshot_entries VALUES
 ('00000000-0000-4000-8000-000000000008','main.tex','file','00000000-0000-4000-8000-000000000006');
INSERT INTO document_jobs(id,project_id,requested_by,job_type,snapshot_id,idempotency_key,request_hash) VALUES
 ('00000000-0000-4000-8000-000000000009','00000000-0000-4000-8000-000000000004','00000000-0000-4000-8000-000000000001','pdf','00000000-0000-4000-8000-000000000008','fixture-key-000001',repeat('e',64));
INSERT INTO job_artifacts(id,job_id,artifact_type,storage_key,filename,mime_type,size_bytes,sha256,expires_at) VALUES
 ('00000000-0000-4000-8000-000000000010','00000000-0000-4000-8000-000000000009','pdf','00000000-0000-4000-8000-000000000011','article.pdf','application/pdf',100,repeat('f',64),now()+interval '7 days');
-- Publish result is transactional and fenced in implementation; fixture represents final committed state.
UPDATE document_jobs SET state='succeeded',stage='complete',attempt=1,started_at=now(),finished_at=now() WHERE id='00000000-0000-4000-8000-000000000009';
INSERT INTO job_log_entries(job_id,sequence,level,code,message) VALUES
 ('00000000-0000-4000-8000-000000000009',1,'info','COMPLETED','Compilation completed');
INSERT INTO audit_events(id,actor_id,project_id,action,entity_type,entity_id) VALUES
 ('00000000-0000-4000-8000-000000000012','00000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000004','create_project','project','00000000-0000-4000-8000-000000000004');
INSERT INTO rate_limit_buckets VALUES('login',repeat('a',64),date_trunc('minute',now()),1);
COMMIT;
