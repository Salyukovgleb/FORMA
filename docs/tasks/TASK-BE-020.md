---
id: "BE-020"
title: "Список, поиск, детали, редактирование, удаление"
epic: "EPIC-03"
priority: "P0"
status: "done"
depends_on: ["BE-019"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-PRJ-001", "FR-PRJ-002", "FR-ACL-001"]
api: ["GET /api/v1/projects", "GET /api/v1/projects/{project_id}", "PATCH /api/v1/projects/{project_id}", "DELETE /api/v1/projects/{project_id}", "POST /api/v1/projects/{project_id}/restore"]
database: ["auth_sessions", "project_members", "projects", "users"]
tests: ["BE-020-POS", "BE-020-NEG", "UNIT-API-013", "API-013", "INT-API-013", "SEC-API-013", "UNIT-API-015", "API-015", "INT-API-015", "SEC-API-015", "UNIT-API-016", "API-016", "INT-API-016", "SEC-API-016", "UNIT-API-017", "API-017", "INT-API-017", "SEC-API-017", "UNIT-API-018", "API-018", "INT-API-018", "SEC-API-018"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage", "0009-storage-publication-fencing"]
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
Таблицы runtime: auth_sessions, project_members, projects, users; project_nodes до BE-025 отсутствует.
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: List/search/update/delete/restore следуют revision, ACL и 7-day retention.
- Зафиксировать negative test: Restore после retention; stale delete.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-020-POS`: List/search/update/delete/restore следуют revision, ACL и 7-day retention.
Endpoint tests: UNIT-API-013, API-013, INT-API-013, SEC-API-013, UNIT-API-015, API-015, INT-API-015, SEC-API-015, UNIT-API-016, API-016, INT-API-016, SEC-API-016, UNIT-API-017, API-017, INT-API-017, SEC-API-017, UNIT-API-018, API-018, INT-API-018, SEC-API-018
Реальные API/PostgreSQL и unit assertions реализованы; перечень результатов в evidence.

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
Только после merge статус done. Никаких force push, skip checks или удаления volumes.

## Evidence/results

Реализация и локальные проверки: [evidence](../evidence/BE-020.md). PR #23 merged `fb1ad22` после8 green checks head `c3eb8fd`.

## Risks

Restore после retention; stale delete. Изменение Outcome требует пересмотра зависимых карточек.

## Mini-plan / dependency review — 2026-11-01

BE-019 merged PR #21 с8 green SHA checks. BE-020 planned → ready → in_progress;
изучены contracts/ACL/revision/retention. Код CRUD на момент mini-plan ещё не был реализован.
Source: modules/projects/{application,schemas,router}.py, infrastructure/projects/persistence.py;
вынести общий read/view port при необходимости, tests/integration/test_project_crud.py.
Runtime0003 уже имеет projects/members; nodes/revisions не нужны для metadata CRUD доBE-025.
Не снимать mainNULL CHECK до0004. Новые DB объекты — только через reviewed Alembic revision.

Tests first: owner/editor/viewer/stranger list/read/update/delete/restore matrix; role derived
из owner/membership, чужие project IDs404, visible forbidden403, deleted скрыт от nonowner.
List/search с keyset cursor created_at/id DESC, limit1..100, filter binding actor/q/status;
никаких N+1. Deleted list только owner. Transport role/owner/cursor не даёт доступа.
PATCH требует expected_revision и контрактные title/description; Unicode/NUL validation из core.
Два concurrent update с одной revision →один успех/один409, stale delete без side effects.
DELETE confirm_title + revision, soft status/deleted_at и revision increment; retained quota
не освобождается. Restore owner-only до7d; active409, expired410, stale409; проверить rollback.

Mutations используют guarded RC UoW. Для editor на чужом owned project все нужные User UUID
(actor + owner) lock в сортированном порядке, затем actor session и project: не вводить
cross-user deadlock. Предварительно читать scalar ACL context и отказывать без foreign user lock; locked Project entity
перечитать/populate_existing, не использовать cached stale revision/membership после ожидания.
Authoritative access context строится adapter внутри UoW; policy BE-017 проверяет scope/rights.
updated_at/deleted_at/retention используют текущий DB clock, не старый transaction timestamp.

JSON bounds расширить на реальные PATCH/DELETE/restore paths; синхронизировать DTO/registry/
OpenAPI, auth/ACL evidence и Docker smoke. Jobs ещё отсутствуют: не заявлять fake cancellation
или audit; jobs-delete integration добавить при jobs tasks BE-033/037, durable audit BE-046.
M2 остаётся открытым. После реализации — tests→commit→push→PR→green CI→merge.

## Implementation review — 2026-11-01

Typed service crud.py/cursor.py, SqlProjectCrudStore, runtime DTO/router и shared error handlers.
Policy проверяется до user locks и повторно после project lock; concurrency/rollback/retention
проверены. Runtime Alembic0003 без новых schema objects. Job cancellation/purge/audit не заявлены.

## Completion — 2026-11-01

PR #23 merged `fb1ad22737cab742bfb6696f2a439d2aa8155158`; exact head `c3eb8fd65c46240bb893406145774e50c1bfa739`,8 SUCCESS checks, run41257627358.
