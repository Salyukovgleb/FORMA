---
id: "BE-044"
title: "Export API, download, quotas, deterministic job results"
epic: "EPIC-06"
priority: "P0"
status: "planned"
depends_on: ["BE-037", "BE-042", "BE-043"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-DOC-002", "FR-DOC-003"]
api: ["POST /api/v1/projects/{project_id}/exports"]
database: ["document_jobs", "project_snapshots", "projects", "snapshot_entries"]
tests: ["BE-044-POS", "BE-044-NEG", "UNIT-API-039", "API-039", "INT-API-039", "SEC-API-039"]
adr: ["0001-modular-monolith", "0004-isolated-document-processing"]
---

# BE-044 — Export API, download, quotas, deterministic job results

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Export API, download, quotas, deterministic job results. Требования: FR-DOC-002, FR-DOC-003. Цель — следующий проверяемый инкремент milestone M5.

## Outcome

Export API выдаёт job и результаты с quotas/idempotency; repeated key не запускает дубль.

## Preconditions

Зависимости: BE-037, BE-042, BE-043. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/infrastructure/conversion/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: POST /api/v1/projects/{project_id}/exports
Таблицы API: document_jobs, project_snapshots, projects, snapshot_entries
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Export API выдаёт job и результаты с quotas/idempotency; repeated key не запускает дубль.
- Зафиксировать negative test: Quota race и stale project revision.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-044-POS`: Export API выдаёт job и результаты с quotas/idempotency; repeated key не запускает дубль.
Endpoint tests: UNIT-API-039, API-039, INT-API-039, SEC-API-039
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-044-NEG`: Quota race и stale project revision.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Export API выдаёт job и результаты с quotas/idempotency; repeated key не запускает дубль. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Quota race и stale project revision. Изменение Outcome требует пересмотра зависимых карточек.
