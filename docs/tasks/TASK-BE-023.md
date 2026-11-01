---
id: "BE-023"
title: "Участники, роли, запрет потери owner, permission tests"
epic: "EPIC-03"
priority: "P0"
status: "in_review"
depends_on: ["BE-019", "BE-017"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-PRJ-001", "FR-PRJ-002", "FR-ACL-001"]
api: ["GET /api/v1/projects/{project_id}/members", "POST /api/v1/projects/{project_id}/members", "PATCH /api/v1/projects/{project_id}/members/{user_id}", "DELETE /api/v1/projects/{project_id}/members/{user_id}"]
database: ["project_members", "projects", "users"]
tests: ["BE-023-POS", "BE-023-NEG", "UNIT-API-034", "API-034", "INT-API-034", "SEC-API-034", "UNIT-API-035", "API-035", "INT-API-035", "SEC-API-035", "UNIT-API-036", "API-036", "INT-API-036", "SEC-API-036", "UNIT-API-037", "API-037", "INT-API-037", "SEC-API-037"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-023 — Участники, роли, запрет потери owner, permission tests

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Участники, роли, запрет потери owner, permission tests. Требования: FR-PRJ-001, FR-PRJ-002, FR-ACL-001. Цель — следующий проверяемый инкремент milestone M2.

## Outcome

Grant/change/remove и self-leave не допускают owner loss или privilege escalation.

## Preconditions

Зависимости: BE-019, BE-017. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/modules/projects/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: GET /api/v1/projects/{project_id}/members, POST /api/v1/projects/{project_id}/members, PATCH /api/v1/projects/{project_id}/members/{user_id}, DELETE /api/v1/projects/{project_id}/members/{user_id}
Таблицы API: project_members, projects, users
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Grant/change/remove и self-leave не допускают owner loss или privilege escalation.
- Зафиксировать negative test: Owner self-remove, editor grant.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-023-POS`: Grant/change/remove и self-leave не допускают owner loss или privilege escalation.
Endpoint tests: UNIT-API-034, API-034, INT-API-034, SEC-API-034, UNIT-API-035, API-035, INT-API-035, SEC-API-035, UNIT-API-036, API-036, INT-API-036, SEC-API-036, UNIT-API-037, API-037, INT-API-037, SEC-API-037
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-023-NEG`: Owner self-remove, editor grant.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Grant/change/remove и self-leave не допускают owner loss или privilege escalation. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
поведение совпадает с DTO/DDL/ACL; нет незакрытого critical security дефекта.

## Documentation updates

Обновить соответствующий нумерованный документ, endpoint registry при API impact,
DB dictionary при schema impact, [STATUS](STATUS.md) и CHANGELOG для значимого изменения.

## Git/CI checklist

Feature branch → meaningful tests → scoped implementation → lint/types/relevant suites →
diff/secret review → Conventional Commit → push → PR → green SHA checks → required review/merge.
До merge статус не done. Никаких force push, skip checks или удаления volumes.

## Evidence/results

[Evidence](../evidence/BE-023.md); local/CI verification pending; not done before merge.

## Risks

Owner self-remove, editor grant. Изменение Outcome требует пересмотра зависимых карточек.

## Mini-plan — 2026-11-01
User explicitly promotes planned→ready; BE-019/017 done; ready→in_progress.
Read ACL policy, API-034..037 DTO/registry, runtime0003 ER, threat model.
Tests first: reader listing, owner grant/change/remove, self-leave, owner immutable,
foreign404/visible403, deleted404, duplicate race,50 cap and rollback.
Files: projects/member_{schemas,application,router}.py, infrastructure/projects/members.py,
tests/integration/test_members.py; reuse guarded RC UoW and sorted actor/owner locks,
project lock then fresh ACL. No migration; membership does not change project revision.
Sync canonical DTO/registry/docs/status/evidence and security target.
