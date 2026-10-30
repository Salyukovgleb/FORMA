# Границы модулей

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

| Модуль | Владеет | Предоставляет | Зависит |
|---|---|---|---|
| identity | users, auth_sessions, used_refresh_tokens | Authenticate, RevokeSession | shared UoW |
| access | project_members policy | RequireProjectPermission | identity principal, projects ownership |
| projects | projects, template manifest | CreateProject, UpdateSettings | access, file creation port |
| project_files | project_nodes, file_revisions | SaveFileContent, MoveProjectNode, PinRevisions | access, storage port |
| documents | project_snapshots, snapshot_entries | RequestCompilation, RequestExport | access, files read port, jobs enqueue port |
| jobs | document_jobs, job_artifacts, job_log_entries | ClaimJob, CompleteJob, CancelJob | storage, compiler/exporter ports |
| audit | audit_events | RecordAuditEvent | current transaction |

Все вызовы внутри процесса. Оркестрация межмодульного UoW на application layer;
никакого HTTP между модулями. Identity не импортирует projects; policy принимает
Principal и ProjectAccessContext. Общие UUID/clock/UoW/error value types — shared.
SQLAlchemy adapters используют одну session use case. Для MVP sync SQLAlchemy + psycopg:
синхронные handlers FastAPI работают в thread pool; upload streaming может быть async,
но DB-часть отдельно выполняется в thread pool. Не вызывать sync DB в event loop.
Worker — синхронный процесс. DI через FastAPI Depends, без дополнительного контейнера.

Protocols: FileStorage.publish/open/delete; ProjectRepository.get_for_update;
NodeRepository.find_in_project; JobRepository.claim/fenced_update;
DocumentCompiler.compile; DocxExporter.export. Domain entities содержат инварианты,
адаптеры только выполняют I/O. Return types — конкретные dataclasses/DTO, не Any.
