---
id: "BE-022"
title: "Настройки проекта и проверка `main_file_id`"
epic: "EPIC-03"
priority: "P0"
status: "planned"
depends_on: ["BE-020", "BE-025"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-PRJ-001", "FR-PRJ-002", "FR-ACL-001"]
api: ["GET /api/v1/projects/{project_id}/settings", "PATCH /api/v1/projects/{project_id}/settings"]
database: ["project_members", "project_nodes", "projects"]
tests: ["BE-022-POS", "BE-022-NEG", "UNIT-API-019", "API-019", "INT-API-019", "SEC-API-019", "UNIT-API-020", "API-020", "INT-API-020", "SEC-API-020"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-022 — Настройки проекта и проверка `main_file_id`

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Настройки проекта и проверка `main_file_id`. Требования: FR-PRJ-001, FR-PRJ-002, FR-ACL-001. Цель — следующий проверяемый инкремент milestone M2.

## Outcome

Нельзя назначить чужой, удалённый или не-tex main; engine whitelist.

## Preconditions

Зависимости: BE-020, BE-025. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/modules/projects/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: GET /api/v1/projects/{project_id}/settings, PATCH /api/v1/projects/{project_id}/settings
Таблицы API: project_members, project_nodes, projects
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Нельзя назначить чужой, удалённый или не-tex main; engine whitelist.
- Зафиксировать negative test: Folder/foreign main_file_id.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-022-POS`: Нельзя назначить чужой, удалённый или не-tex main; engine whitelist.
Endpoint tests: UNIT-API-019, API-019, INT-API-019, SEC-API-019, UNIT-API-020, API-020, INT-API-020, SEC-API-020
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-022-NEG`: Folder/foreign main_file_id.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Нельзя назначить чужой, удалённый или не-tex main; engine whitelist. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Folder/foreign main_file_id. Изменение Outcome требует пересмотра зависимых карточек.
