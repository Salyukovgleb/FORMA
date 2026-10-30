---
id: "BE-020"
title: "Список, поиск, детали, редактирование, удаление"
epic: "EPIC-03"
priority: "P0"
status: "planned"
depends_on: ["BE-019"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-PRJ-001", "FR-PRJ-002", "FR-ACL-001"]
api: ["GET /api/v1/projects", "GET /api/v1/projects/{project_id}", "PATCH /api/v1/projects/{project_id}", "DELETE /api/v1/projects/{project_id}", "POST /api/v1/projects/{project_id}/restore"]
database: ["project_members", "project_nodes", "projects"]
tests: ["BE-020-POS", "BE-020-NEG", "UNIT-API-013", "API-013", "INT-API-013", "SEC-API-013", "UNIT-API-015", "API-015", "INT-API-015", "SEC-API-015", "UNIT-API-016", "API-016", "INT-API-016", "SEC-API-016", "UNIT-API-017", "API-017", "INT-API-017", "SEC-API-017", "UNIT-API-018", "API-018", "INT-API-018", "SEC-API-018"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-020 — Список, поиск, детали, редактирование, удаление

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Список, поиск, детали, редактирование, удаление. Требования: FR-PRJ-001, FR-PRJ-002, FR-ACL-001. Цель — следующий проверяемый инкремент milestone M2.

## Outcome

List/search/update/delete/restore следуют revision, ACL и 7-day retention.

## Preconditions

Зависимости: BE-019. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/modules/projects/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: GET /api/v1/projects, GET /api/v1/projects/{project_id}, PATCH /api/v1/projects/{project_id}, DELETE /api/v1/projects/{project_id}, POST /api/v1/projects/{project_id}/restore
Таблицы API: project_members, project_nodes, projects
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: List/search/update/delete/restore следуют revision, ACL и 7-day retention.
- Зафиксировать negative test: Restore после retention; stale delete.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-020-POS`: List/search/update/delete/restore следуют revision, ACL и 7-day retention.
Endpoint tests: UNIT-API-013, API-013, INT-API-013, SEC-API-013, UNIT-API-015, API-015, INT-API-015, SEC-API-015, UNIT-API-016, API-016, INT-API-016, SEC-API-016, UNIT-API-017, API-017, INT-API-017, SEC-API-017, UNIT-API-018, API-018, INT-API-018, SEC-API-018
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-020-NEG`: Restore после retention; stale delete.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

List/search/update/delete/restore следуют revision, ACL и 7-day retention. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Restore после retention; stale delete. Изменение Outcome требует пересмотра зависимых карточек.
