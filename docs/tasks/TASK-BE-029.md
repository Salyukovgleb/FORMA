---
id: "BE-029"
title: "Неизменяемые revisions: список, чтение, восстановление"
epic: "EPIC-04"
priority: "P0"
status: "planned"
depends_on: ["BE-027", "BE-028"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-FILE-001", "FR-FILE-002", "NFR-CONC-001"]
api: ["GET /api/v1/projects/{project_id}/files/{file_id}/revisions", "GET /api/v1/projects/{project_id}/files/{file_id}/revisions/{revision}", "POST /api/v1/projects/{project_id}/files/{file_id}/revisions/{revision}/restore"]
database: ["file_revisions", "project_nodes", "projects"]
tests: ["BE-029-POS", "BE-029-NEG", "UNIT-API-031", "API-031", "INT-API-031", "SEC-API-031", "UNIT-API-032", "API-032", "INT-API-032", "SEC-API-032", "UNIT-API-033", "API-033", "INT-API-033", "SEC-API-033"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-029 — Неизменяемые revisions: список, чтение, восстановление

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Неизменяемые revisions: список, чтение, восстановление. Требования: FR-FILE-001, FR-FILE-002, NFR-CONC-001. Цель — следующий проверяемый инкремент milestone M3.

## Outcome

История immutable, restore создаёт N+1; pinned old revision не удаляется GC.

## Preconditions

Зависимости: BE-027, BE-028. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/modules/project_files/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: GET /api/v1/projects/{project_id}/files/{file_id}/revisions, GET /api/v1/projects/{project_id}/files/{file_id}/revisions/{revision}, POST /api/v1/projects/{project_id}/files/{file_id}/revisions/{revision}/restore
Таблицы API: file_revisions, project_nodes, projects
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: История immutable, restore создаёт N+1; pinned old revision не удаляется GC.
- Зафиксировать negative test: Restore binary415 и pruned revision404.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-029-POS`: История immutable, restore создаёт N+1; pinned old revision не удаляется GC.
Endpoint tests: UNIT-API-031, API-031, INT-API-031, SEC-API-031, UNIT-API-032, API-032, INT-API-032, SEC-API-032, UNIT-API-033, API-033, INT-API-033, SEC-API-033
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-029-NEG`: Restore binary415 и pruned revision404.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

История immutable, restore создаёт N+1; pinned old revision не удаляется GC. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Restore binary415 и pruned revision404. Изменение Outcome требует пересмотра зависимых карточек.
