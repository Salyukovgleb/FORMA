# Словарь PostgreSQL

Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30. Связи: BE-004, ADR-0002/0003.

Источник: [DDL](database/schema.sql), [валидные примеры всех таблиц](database/examples.sql), [инварианты](05_DATA_MODEL.md). SQL definitions ниже полностью определяют тип, NULL/default, CHECK/FK/ON DELETE. Отсутствующий DEFAULT означает обязательную передачу значения (кроме nullable). Отсутствующий ON DELETE у FK означает NO ACTION.

## users

Модуль: `identity`. Пример INSERT: [examples.sql](database/examples.sql).

| Колонка | SQL definition (тип / NULL / default / constraints) | Назначение |
|---|---|---|
| `id` | `uuid PRIMARY KEY` | Серверный UUID сущности |
| `email` | `varchar(254) NOT NULL UNIQUE CHECK (email = lower(btrim(email)))` | Нормализованный адрес входа |
| `password_hash` | `text NOT NULL` | Версионированный scrypt hash с salt/params |
| `display_name` | `varchar(100) NOT NULL CHECK (length(display_name)>0)` | Отображаемое имя |
| `is_active` | `boolean NOT NULL DEFAULT true` | Флаг разрешённого входа |
| `created_at` | `timestamptz NOT NULL DEFAULT now()` | Время создания UTC |
| `updated_at` | `timestamptz NOT NULL DEFAULT now()` | Последнее изменение UTC, обновляет use case |

Табличные ограничения:
```sql
-- PK/FK/CHECK указаны в строках колонок
```

Индексы: PK/UNIQUE индексы из определения; дополнительные не нужны для MVP.

Конкурентность/retention: mutations внутри UoW с блокировками согласно [очереди](14_JOB_QUEUE_AND_RETRIES.md) и [storage](11_LOCAL_FILE_STORAGE.md).

## auth_sessions

Модуль: `identity`. Пример INSERT: [examples.sql](database/examples.sql).

| Колонка | SQL definition (тип / NULL / default / constraints) | Назначение |
|---|---|---|
| `id` | `uuid PRIMARY KEY` | Серверный UUID сущности |
| `user_id` | `uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT` | Пользователь связи/сессии |
| `refresh_token_hash` | `char(64) NOT NULL UNIQUE` | SHA-256 действующего refresh token |
| `csrf_token_hash` | `char(64) NOT NULL` | SHA-256 CSRF token |
| `expires_at` | `timestamptz NOT NULL` | Абсолютный срок истечения UTC |
| `revoked_at` | `timestamptz` | Время отзыва, null пока не отозвана |
| `created_at` | `timestamptz NOT NULL DEFAULT now()` | Время создания UTC |
| `rotated_at` | `timestamptz NOT NULL DEFAULT now()` | Последняя ротация UTC |

Табличные ограничения:
```sql
CHECK (expires_at > created_at)
```

Индексы: `CREATE INDEX auth_sessions_user ON auth_sessions(user_id, expires_at);`

Конкурентность/retention: mutations внутри UoW с блокировками согласно [очереди](14_JOB_QUEUE_AND_RETRIES.md) и [storage](11_LOCAL_FILE_STORAGE.md).

## used_refresh_tokens

Модуль: `identity`. Пример INSERT: [examples.sql](database/examples.sql).

| Колонка | SQL definition (тип / NULL / default / constraints) | Назначение |
|---|---|---|
| `token_hash` | `char(64) PRIMARY KEY` | SHA-256 уже использованного refresh token |
| `session_id` | `uuid NOT NULL REFERENCES auth_sessions(id) ON DELETE CASCADE` | Семейство ротации |
| `expires_at` | `timestamptz NOT NULL` | Абсолютный срок истечения UTC |

Табличные ограничения:
```sql
-- PK/FK/CHECK указаны в строках колонок
```

Индексы: PK/UNIQUE индексы из определения; дополнительные не нужны для MVP.

Конкурентность/retention: mutations внутри UoW с блокировками согласно [очереди](14_JOB_QUEUE_AND_RETRIES.md) и [storage](11_LOCAL_FILE_STORAGE.md).

## projects

Модуль: `projects`. Пример INSERT: [examples.sql](database/examples.sql).

| Колонка | SQL definition (тип / NULL / default / constraints) | Назначение |
|---|---|---|
| `id` | `uuid PRIMARY KEY` | Серверный UUID сущности |
| `owner_id` | `uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT` | Единственный неизменяемый владелец |
| `title` | `varchar(200) NOT NULL CHECK (length(btrim(title))>0)` | Название проекта |
| `description` | `varchar(2000) NOT NULL DEFAULT ''` | Описание проекта |
| `main_file_id` | `uuid` | Главный live tex-файл либо null |
| `engine` | `text NOT NULL DEFAULT 'xelatex' CHECK (engine IN ('pdflatex','xelatex','lualatex'))` | Выбранный LaTeX engine |
| `status` | `text NOT NULL DEFAULT 'active' CHECK (status IN ('active','deleted'))` | active/deleted lifecycle |
| `revision` | `bigint NOT NULL DEFAULT 1 CHECK (revision>0)` | Монотонная версия соответствующей сущности |
| `created_at` | `timestamptz NOT NULL DEFAULT now()` | Время создания UTC |
| `updated_at` | `timestamptz NOT NULL DEFAULT now()` | Последнее изменение UTC, обновляет use case |
| `deleted_at` | `timestamptz` | Время мягкого удаления UTC |

Табличные ограничения:
```sql
CHECK ((status='deleted') = (deleted_at IS NOT NULL))
```

Индексы: `CREATE INDEX projects_owner ON projects(owner_id, created_at DESC, id DESC);`

Конкурентность/retention: mutations внутри UoW с блокировками согласно [очереди](14_JOB_QUEUE_AND_RETRIES.md) и [storage](11_LOCAL_FILE_STORAGE.md).

## project_members

Модуль: `access`. Пример INSERT: [examples.sql](database/examples.sql).

| Колонка | SQL definition (тип / NULL / default / constraints) | Назначение |
|---|---|---|
| `project_id` | `uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE` | Проект-владелец объекта |
| `user_id` | `uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT` | Пользователь связи/сессии |
| `role` | `text NOT NULL CHECK (role IN ('editor','viewer'))` | editor/viewer; owner определяется projects.owner_id |
| `invited_by` | `uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT` | Кто выдал доступ |
| `created_at` | `timestamptz NOT NULL DEFAULT now()` | Время создания UTC |

Табличные ограничения:
```sql
PRIMARY KEY (project_id,user_id)
```

Индексы: `CREATE INDEX project_members_user ON project_members(user_id, project_id);`

Конкурентность/retention: mutations внутри UoW с блокировками согласно [очереди](14_JOB_QUEUE_AND_RETRIES.md) и [storage](11_LOCAL_FILE_STORAGE.md).

## project_nodes

Модуль: `project_files`. Пример INSERT: [examples.sql](database/examples.sql).

| Колонка | SQL definition (тип / NULL / default / constraints) | Назначение |
|---|---|---|
| `id` | `uuid PRIMARY KEY` | Серверный UUID сущности |
| `project_id` | `uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE` | Проект-владелец объекта |
| `parent_id` | `uuid` | Папка-родитель; null означает root |
| `name` | `varchar(255) NOT NULL CHECK (name NOT IN ('','.','..') AND name !~ '[/\\]')` | NFC basename |
| `node_type` | `text NOT NULL CHECK (node_type IN ('file','folder'))` | file/folder |
| `logical_path` | `varchar(1024) NOT NULL CHECK (logical_path !~ '^/' AND logical_path !~ '(^&#124;/)\.\.(/&#124;$)')` | Относительный материализованный POSIX путь |
| `media_type` | `varchar(100)` | MIME файла; null для папки |
| `revision` | `bigint NOT NULL DEFAULT 1 CHECK (revision>0)` | Монотонная версия соответствующей сущности |
| `created_at` | `timestamptz NOT NULL DEFAULT now()` | Время создания UTC |
| `updated_at` | `timestamptz NOT NULL DEFAULT now()` | Последнее изменение UTC, обновляет use case |
| `deleted_at` | `timestamptz` | Время мягкого удаления UTC |

Табличные ограничения:
```sql
UNIQUE (project_id,id);
FOREIGN KEY (project_id,parent_id) REFERENCES project_nodes(project_id,id) DEFERRABLE INITIALLY DEFERRED;
CHECK (parent_id IS DISTINCT FROM id);
CHECK ((node_type='folder' AND media_type IS NULL) OR (node_type='file' AND media_type IS NOT NULL))
```

Индексы: `CREATE UNIQUE INDEX nodes_path_live ON project_nodes(project_id,logical_path) WHERE deleted_at IS NULL;` `CREATE UNIQUE INDEX nodes_siblings_live ON project_nodes(project_id,coalesce(parent_id,'00000000-0000-0000-0000-000000000000'::uuid),name) WHERE deleted_at IS NULL;`

Конкурентность/retention: mutations внутри UoW с блокировками согласно [очереди](14_JOB_QUEUE_AND_RETRIES.md) и [storage](11_LOCAL_FILE_STORAGE.md).

## file_revisions

Модуль: `project_files`. Пример INSERT: [examples.sql](database/examples.sql).

| Колонка | SQL definition (тип / NULL / default / constraints) | Назначение |
|---|---|---|
| `id` | `uuid PRIMARY KEY` | Серверный UUID сущности |
| `node_id` | `uuid NOT NULL REFERENCES project_nodes(id) ON DELETE CASCADE` | Узел-владелец содержимого |
| `revision` | `bigint NOT NULL CHECK (revision>0)` | Монотонная версия соответствующей сущности |
| `content_storage_key` | `uuid NOT NULL UNIQUE` | UUID физического immutable blob |
| `content_hash` | `char(64) NOT NULL CHECK (content_hash ~ '^[0-9a-f]{64}$')` | SHA-256 bytes lower hex |
| `size_bytes` | `bigint NOT NULL CHECK (size_bytes>=0 AND size_bytes<=20971520)` | Размер bytes |
| `author_id` | `uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT` | Автор версии |
| `created_at` | `timestamptz NOT NULL DEFAULT now()` | Время создания UTC |

Табличные ограничения:
```sql
UNIQUE (node_id,revision)
```

Индексы: PK/UNIQUE индексы из определения; дополнительные не нужны для MVP.

Конкурентность/retention: immutable append; удаление только retention GC, pinned references сохраняются.

## project_snapshots

Модуль: `documents`. Пример INSERT: [examples.sql](database/examples.sql).

| Колонка | SQL definition (тип / NULL / default / constraints) | Назначение |
|---|---|---|
| `id` | `uuid PRIMARY KEY` | Серверный UUID сущности |
| `project_id` | `uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE` | Проект-владелец объекта |
| `project_revision` | `bigint NOT NULL CHECK (project_revision>0)` | Версия проекта в момент snapshot |
| `main_path` | `varchar(1024)` | Зафиксированный логический путь main; null допустим для ZIP |
| `engine` | `text NOT NULL CHECK (engine IN ('pdflatex','xelatex','lualatex'))` | Выбранный LaTeX engine |
| `created_at` | `timestamptz NOT NULL DEFAULT now()` | Время создания UTC |

Табличные ограничения:
```sql
-- PK/FK/CHECK указаны в строках колонок
```

Индексы: PK/UNIQUE индексы из определения; дополнительные не нужны для MVP.

Конкурентность/retention: immutable append; удаление только retention GC, pinned references сохраняются.

## snapshot_entries

Модуль: `documents`. Пример INSERT: [examples.sql](database/examples.sql).

| Колонка | SQL definition (тип / NULL / default / constraints) | Назначение |
|---|---|---|
| `snapshot_id` | `uuid NOT NULL REFERENCES project_snapshots(id) ON DELETE CASCADE` | Immutable snapshot |
| `logical_path` | `varchar(1024) NOT NULL` | Относительный материализованный POSIX путь |
| `node_type` | `text NOT NULL CHECK (node_type IN ('file','folder'))` | file/folder |
| `revision_id` | `uuid REFERENCES file_revisions(id) ON DELETE RESTRICT` | Удерживаемая immutable версия; null у папки |

Табличные ограничения:
```sql
PRIMARY KEY (snapshot_id,logical_path);
CHECK ((node_type='file') = (revision_id IS NOT NULL))
```

Индексы: PK/UNIQUE индексы из определения; дополнительные не нужны для MVP.

Конкурентность/retention: immutable append; удаление только retention GC, pinned references сохраняются.

## document_jobs

Модуль: `jobs`. Пример INSERT: [examples.sql](database/examples.sql).

| Колонка | SQL definition (тип / NULL / default / constraints) | Назначение |
|---|---|---|
| `id` | `uuid PRIMARY KEY` | Серверный UUID сущности |
| `project_id` | `uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE` | Проект-владелец объекта |
| `requested_by` | `uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT` | Пользователь, запросивший job |
| `job_type` | `text NOT NULL CHECK (job_type IN ('pdf','docx','zip'))` | pdf/docx/zip |
| `state` | `text NOT NULL DEFAULT 'queued' CHECK (state IN ('queued','running','retry_wait','succeeded','failed','cancelled'))` | Состояние очереди |
| `stage` | `text NOT NULL DEFAULT 'waiting' CHECK (stage IN ('waiting','snapshot','processing','publishing','complete'))` | Крупный шаг обработки, не процент |
| `snapshot_id` | `uuid NOT NULL REFERENCES project_snapshots(id) ON DELETE RESTRICT` | Immutable snapshot |
| `idempotency_key` | `varchar(128) NOT NULL` | Клиентский ключ повтора |
| `request_hash` | `char(64) NOT NULL` | SHA-256 route+canonical request |
| `attempt` | `integer NOT NULL DEFAULT 0 CHECK (attempt>=0)` | Число начатых попыток |
| `max_attempts` | `integer NOT NULL DEFAULT 3 CHECK (max_attempts BETWEEN 1 AND 3)` | Максимум попыток |
| `lease_token` | `uuid` | Fencing UUID текущей попытки |
| `lease_until` | `timestamptz` | Срок владения UTC |
| `heartbeat_at` | `timestamptz` | Последний принятый heartbeat |
| `next_run_at` | `timestamptz NOT NULL DEFAULT now()` | Не раньше этого времени claim |
| `cancellation_requested` | `boolean NOT NULL DEFAULT false` | Запрошена отмена running job |
| `queued_at` | `timestamptz NOT NULL DEFAULT now()` | Время enqueue UTC |
| `started_at` | `timestamptz` | Первый старт UTC |
| `finished_at` | `timestamptz` | Terminal timestamp UTC |
| `error_code` | `varchar(80)` | Машинная причина terminal failure |
| `error_message` | `varchar(2000)` | Безопасный текст ошибки |
| `options_json` | `jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(options_json)='object')` | Версионированные параметры: reference_id/toolchain_digest для exports |

Табличные ограничения:
```sql
UNIQUE (project_id,requested_by,idempotency_key);
CHECK (attempt<=max_attempts);
CHECK ((state='running') = (lease_token IS NOT NULL AND lease_until IS NOT NULL));
CHECK ((state IN ('succeeded','failed','cancelled')) = (finished_at IS NOT NULL))
```

Индексы: `CREATE INDEX jobs_claim ON document_jobs(state, queued_at) WHERE state IN ('queued','retry_wait');` `CREATE INDEX jobs_project ON document_jobs(project_id, queued_at DESC,id DESC);` `CREATE INDEX jobs_requester ON document_jobs(requested_by,state);` `CREATE INDEX jobs_expired ON document_jobs(lease_until) WHERE state='running';`

Конкурентность/retention: mutations внутри UoW с блокировками согласно [очереди](14_JOB_QUEUE_AND_RETRIES.md) и [storage](11_LOCAL_FILE_STORAGE.md).

## job_artifacts

Модуль: `jobs`. Пример INSERT: [examples.sql](database/examples.sql).

| Колонка | SQL definition (тип / NULL / default / constraints) | Назначение |
|---|---|---|
| `id` | `uuid PRIMARY KEY` | Серверный UUID сущности |
| `job_id` | `uuid NOT NULL REFERENCES document_jobs(id) ON DELETE CASCADE` | Родительское задание |
| `artifact_type` | `text NOT NULL CHECK (artifact_type IN ('pdf','docx','zip'))` | Формат результата |
| `storage_key` | `uuid NOT NULL UNIQUE` | UUID immutable output blob |
| `filename` | `varchar(255) NOT NULL` | Безопасное имя скачивания |
| `mime_type` | `varchar(100) NOT NULL` | MIME результата |
| `size_bytes` | `bigint NOT NULL CHECK (size_bytes>=0 AND size_bytes<=104857600)` | Размер bytes |
| `sha256` | `char(64) NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$')` | SHA-256 результата |
| `created_at` | `timestamptz NOT NULL DEFAULT now()` | Время создания UTC |
| `expires_at` | `timestamptz NOT NULL` | Абсолютный срок истечения UTC |

Табличные ограничения:
```sql
UNIQUE (job_id,artifact_type);
CHECK (expires_at>created_at)
```

Индексы: PK/UNIQUE индексы из определения; дополнительные не нужны для MVP.

Конкурентность/retention: immutable append; удаление только retention GC, pinned references сохраняются.

## job_log_entries

Модуль: `jobs`. Пример INSERT: [examples.sql](database/examples.sql).

| Колонка | SQL definition (тип / NULL / default / constraints) | Назначение |
|---|---|---|
| `job_id` | `uuid NOT NULL REFERENCES document_jobs(id) ON DELETE CASCADE` | Родительское задание |
| `sequence` | `bigint NOT NULL CHECK (sequence>0)` | Монотонный номер записи job |
| `level` | `text NOT NULL CHECK (level IN ('info','warning','error'))` | info/warning/error |
| `code` | `varchar(80) NOT NULL` | Машинный код диагностики |
| `message` | `varchar(2000) NOT NULL` | Ограниченный очищенный текст |
| `file` | `varchar(1024)` | Путь из snapshot либо null |
| `line` | `integer CHECK (line>0)` | Достоверная строка начиная с 1 либо null |
| `created_at` | `timestamptz NOT NULL DEFAULT now()` | Время создания UTC |

Табличные ограничения:
```sql
PRIMARY KEY (job_id,sequence)
```

Индексы: PK/UNIQUE индексы из определения; дополнительные не нужны для MVP.

Конкурентность/retention: immutable append; удаление только retention GC, pinned references сохраняются.

## audit_events

Модуль: `audit`. Пример INSERT: [examples.sql](database/examples.sql).

| Колонка | SQL definition (тип / NULL / default / constraints) | Назначение |
|---|---|---|
| `id` | `uuid PRIMARY KEY` | Серверный UUID сущности |
| `actor_id` | `uuid REFERENCES users(id) ON DELETE SET NULL` | Автор события, nullable после purge user |
| `project_id` | `uuid REFERENCES projects(id) ON DELETE SET NULL` | Проект-владелец объекта |
| `action` | `varchar(100) NOT NULL` | Use-case action name |
| `entity_type` | `varchar(80) NOT NULL` | Тип audit объекта |
| `entity_id` | `uuid NOT NULL` | UUID audit объекта, сохраняется после purge |
| `metadata_json` | `jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata_json)='object')` | Whitelist metadata без секретов/содержимого |
| `created_at` | `timestamptz NOT NULL DEFAULT now()` | Время создания UTC |

Табличные ограничения:
```sql
-- PK/FK/CHECK указаны в строках колонок
```

Индексы: `CREATE INDEX audit_project ON audit_events(project_id,created_at DESC);`

Конкурентность/retention: immutable append; удаление только retention GC, pinned references сохраняются.

## rate_limit_buckets

Модуль: `identity`. Пример INSERT: [examples.sql](database/examples.sql).

| Колонка | SQL definition (тип / NULL / default / constraints) | Назначение |
|---|---|---|
| `scope` | `varchar(80) NOT NULL` | Категория rate limit |
| `subject_hash` | `char(64) NOT NULL` | HMAC идентификатора/IP |
| `window_start` | `timestamptz NOT NULL` | Начало fixed window UTC |
| `count` | `integer NOT NULL CHECK (count>=0)` | Счётчик запросов |

Табличные ограничения:
```sql
PRIMARY KEY (scope,subject_hash,window_start)
```

Индексы: PK/UNIQUE индексы из определения; дополнительные не нужны для MVP.

Конкурентность/retention: mutations внутри UoW с блокировками согласно [очереди](14_JOB_QUEUE_AND_RETRIES.md) и [storage](11_LOCAL_FILE_STORAGE.md).

## Индексы, рост и удаления

users unique email — login lookup; auth user index — revoke-all; members reverse index — projects list. nodes live indexes — tree paths/collisions; revisions unique(node,revision) — latest/history. jobs indexes — claim/status/lease cleanup; audit project/time — расследование. Индексы увеличивают write cost; EXPLAIN на BE-048 обязателен.

CASCADE только для принадлежащих project/session/job записей. RESTRICT сохраняет users/revisions/snapshots от раннего purge. audit SET NULL сохраняет событие после удаления проекта. Физические blobs никогда не удаляются SQL cascade: их удаляет отдельный GC. Retention 7/30/90 суток определён в storage/operations.

При 1000 пользователей планировать 20 млн revisions, до 300 тыс jobs за месяц при 10 jobs/user/day и до 300 млн log rows в худшем cap; это upper bound, поэтому log cap и purge обязательны. Рост snapshots примерно jobs × file count; удалить entries с jobs через 30 дней. Если фактический размер выходит за бюджет, сначала снижать retention/лимиты, затем ADR по partitioning.

SQLAlchemy 2.x модели planned: явные Mapped/ mapped_column, UUID(as_uuid=True), DateTime(timezone=True), ForeignKeyConstraint для composite FK. Domain classes не наследуют ORM. Реализация ORM и Alembic — BE-011/014/019/025/031, не фаза A.

## Реализованный срез BE-011

users/auth_sessions/used_refresh_tokens/rate_limit_buckets имеют typed ORM models
в src/forma_backend/infrastructure/database/models.py и две Alembic revisions.
Колонки/FK/defaults соответствуют DDL; именованы ck_users_email_normalized,
ck_users_display_name, ck_sessions_expiry, ck_rate_count для сопровождаемости.
Остальные таблицы — design planned, не считать их мигрированными после upgrade head.

BE-015 runtime: auth_sessions содержит только SHA256 refresh/CSRF; history хранит used hash
до absolute expiry. Logout/revoke не меняют rotated_at и не продлевают expiry.
Rate bucket scopes register/login-ip/login-email/refresh-session; refresh quota commit
выполняется в session transaction без дополнительного connection/lock-order inversion.

BE-016: profile/password writes обновляют users.updated_at явно. User row lock сериализует
login и password-change; password_hash + revoke-all атомарны, rollback сохраняет оба состояния.
Password-change scope rate_limit_buckets: HMAC user ID,10/15min. Новых колонок/миграций нет.

BE-018: rate_limit_buckets UPSERT использует DB statement clock. Bounded cleanup старше24h
не трогает current buckets, locked rows пропускаются; caller управляет commit/rollback.
Новых DB объектов нет. Для крупного объёма оценить expiry index/EXPLAIN на BE-048;
до этого operator cleanup ограничен statement timeout2s и не запускается на каждом request.

BE-024: DB schema не меняется. Maintenance advisory namespace/key1179603533/1 database-local;
все users этой storage root используют одну DB authority. Reference probe для final blobs —
будущие revision/artifact/snapshot repositories (BE-025/035/047), не фиктивная runtime таблица.
Metadata writes привязываются к dedicated guard connection и explicit lease.commit() (ADR-0009).

BE-019 runtime: projects/project_members typed ORM и Alembic0003. Project defaults active,
revision1, engine xelatex, main_file_idNULL, DB timestamps; title btrim nonempty, engine/status/
revision/deleted timestamp CHECKs. Временный mainNULL CHECK до0004 закрывает отсутствие nodes FK.
Owner FK RESTRICT; members project CASCADE, user/inviter RESTRICT и role editor/viewer only.
Owner не создаётся membership row. Projects owner index включает created_at/id DESC.
Квота count всех retained projects текущего owner, включая deleted, под user row lock;
Session row тоже locked и перепроверяется после user lock. Metadata commit — только guard connection.

CreateProject UoW явно использует READ COMMITTED независимо от server/engine default:
после ожидания user lock count видит предыдущий commit. Regression проверяет concurrent
different-session quota при исходных READ COMMITTED и REPEATABLE READ defaults.

BE-020 schema не меняет: head0003 остаётся6 runtime tables. Read ACL — joined projection;
mutation locked re-read не использует cached stale project/member. Revision CAS дополнительно
проверяется UPDATE ... WHERE revision=previous RETURNING id. updated_at/deleted_at/retention
берутся из clock_timestamp после locks. Successful no-op PATCH тоже увеличивает revision.
Soft-delete сохраняет rows; restore снимает deleted_at; mainNULL CHECK остаётся до0004.


BE-023 reuses runtime0003 projects/project_members/users/auth_sessions; no migration. Owner row is projected from projects.created_at and users.display_name, not inserted into project_members. Membership joined list is ordered by created_at,user_id after owner; guarded RC transaction locks actor/owner users in UUID order, actor session, then project. Writes use current membership after lock and explicit outer commit.
