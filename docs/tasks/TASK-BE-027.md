---
id: "BE-027"
title: "Read/save content, optimistic locking, revision increments"
epic: "EPIC-04"
priority: "P0"
status: "planned"
depends_on: ["BE-025", "BE-026"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-FILE-001", "FR-FILE-002", "NFR-CONC-001"]
api: ["GET /api/v1/projects/{project_id}/files/{file_id}/content", "PUT /api/v1/projects/{project_id}/files/{file_id}/content"]
database: ["file_revisions", "project_nodes", "projects"]
tests: ["BE-027-POS", "BE-027-NEG", "UNIT-API-026", "API-026", "INT-API-026", "SEC-API-026", "UNIT-API-027", "API-027", "INT-API-027", "SEC-API-027"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-027 — Read/save content, optimistic locking, revision increments

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Read/save content, optimistic locking, revision increments. Требования: FR-FILE-001, FR-FILE-002, NFR-CONC-001. Цель — следующий проверяемый инкремент milestone M3.

## Outcome

Два saves expected_revision=N дают один success и один 409 без перезаписи.

## Preconditions

Зависимости: BE-025, BE-026. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/modules/project_files/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: GET /api/v1/projects/{project_id}/files/{file_id}/content, PUT /api/v1/projects/{project_id}/files/{file_id}/content
Таблицы API: file_revisions, project_nodes, projects
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Два saves expected_revision=N дают один success и один 409 без перезаписи.
- Зафиксировать negative test: Stale save и rollback publish.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-027-POS`: Два saves expected_revision=N дают один success и один 409 без перезаписи.
Endpoint tests: UNIT-API-026, API-026, INT-API-026, SEC-API-026, UNIT-API-027, API-027, INT-API-027, SEC-API-027
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-027-NEG`: Stale save и rollback publish.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Два saves expected_revision=N дают один success и один 409 без перезаписи. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Stale save и rollback publish. Изменение Outcome требует пересмотра зависимых карточек.
