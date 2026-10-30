---
id: "BE-037"
title: "Compile API, job status/list/logs/cancel, download"
epic: "EPIC-05"
priority: "P0"
status: "planned"
depends_on: ["BE-023", "BE-032", "BE-033", "BE-035", "BE-036"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-DOC-001", "NFR-SEC-001"]
api: ["POST /api/v1/projects/{project_id}/compilations", "GET /api/v1/projects/{project_id}/jobs", "GET /api/v1/projects/{project_id}/jobs/{job_id}", "GET /api/v1/projects/{project_id}/jobs/{job_id}/logs", "POST /api/v1/projects/{project_id}/jobs/{job_id}/cancel", "GET /api/v1/projects/{project_id}/artifacts/{artifact_id}/download"]
database: ["document_jobs", "job_artifacts", "job_log_entries", "project_snapshots", "projects", "snapshot_entries"]
tests: ["BE-037-POS", "BE-037-NEG", "UNIT-API-038", "API-038", "INT-API-038", "SEC-API-038", "UNIT-API-040", "API-040", "INT-API-040", "SEC-API-040", "UNIT-API-041", "API-041", "INT-API-041", "SEC-API-041", "UNIT-API-042", "API-042", "INT-API-042", "SEC-API-042", "UNIT-API-043", "API-043", "INT-API-043", "SEC-API-043", "UNIT-API-044", "API-044", "INT-API-044", "SEC-API-044"]
adr: ["0001-modular-monolith", "0004-isolated-document-processing"]
---

# BE-037 — Compile API, job status/list/logs/cancel, download

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Compile API, job status/list/logs/cancel, download. Требования: FR-DOC-001, NFR-SEC-001. Цель — следующий проверяемый инкремент milestone M4.

## Outcome

Compile/status/list/logs/cancel/download реализуют 202, ACL и idempotency.

## Preconditions

Зависимости: BE-023, BE-032, BE-033, BE-035, BE-036. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/infrastructure/workers/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: POST /api/v1/projects/{project_id}/compilations, GET /api/v1/projects/{project_id}/jobs, GET /api/v1/projects/{project_id}/jobs/{job_id}, GET /api/v1/projects/{project_id}/jobs/{job_id}/logs, POST /api/v1/projects/{project_id}/jobs/{job_id}/cancel, GET /api/v1/projects/{project_id}/artifacts/{artifact_id}/download
Таблицы API: document_jobs, job_artifacts, job_log_entries, project_snapshots, projects, snapshot_entries
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Compile/status/list/logs/cancel/download реализуют 202, ACL и idempotency.
- Зафиксировать negative test: Idempotency key с другим body.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-037-POS`: Compile/status/list/logs/cancel/download реализуют 202, ACL и idempotency.
Endpoint tests: UNIT-API-038, API-038, INT-API-038, SEC-API-038, UNIT-API-040, API-040, INT-API-040, SEC-API-040, UNIT-API-041, API-041, INT-API-041, SEC-API-041, UNIT-API-042, API-042, INT-API-042, SEC-API-042, UNIT-API-043, API-043, INT-API-043, SEC-API-043, UNIT-API-044, API-044, INT-API-044, SEC-API-044
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-037-NEG`: Idempotency key с другим body.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Compile/status/list/logs/cancel/download реализуют 202, ACL и idempotency. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
поведение совпадает с DTO/DDL/ACL; нет незакрытого critical security дефекта.

## Documentation updates

Обновить соответствующий нумерованный документ, endpoint registry при API impact,
DB dictionary при schema impact, [STATUS](STATUS.md) и CHANGELOG для значимого изменения.

## Git/CI checklist

Feature branch → meaningful tests → scoped implementation → lint/types/relevant suites →
diff/secret review → Conventional Commit → push → PR → green SHA checks → required review/merge.
До merge статус не done. Никаких force push, skip checks или удаления volumes.

## Evidence/results

planned; code/tests/commit/PR/CI отсутствуют, поведение не проверено.

## Risks

Idempotency key с другим body. Изменение Outcome требует пересмотра зависимых карточек.
