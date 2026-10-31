---
id: "BE-017"
title: "Role policy owner/editor/viewer, object-level authorization"
epic: "EPIC-02"
priority: "P0"
status: "in_progress"
depends_on: ["BE-015"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-AUTH-001", "FR-ACL-001"]
api: []
database: []
tests: ["BE-017-POS", "BE-017-NEG"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-017 — Role policy owner/editor/viewer, object-level authorization

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Role policy owner/editor/viewer, object-level authorization. Требования: FR-AUTH-001, FR-ACL-001. Цель — следующий проверяемый инкремент milestone M1.

## Outcome

Policy покрывает owner/editor/viewer и child IDs без утечки чужих проектов.

## Preconditions

Зависимости: BE-015. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/modules/identity/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: Публичный endpoint не добавляется этой задачей.
Таблицы API: Схема/инфраструктурный impact определяется Outcome; целевой DDL в database/schema.sql.
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Policy покрывает owner/editor/viewer и child IDs без утечки чужих проектов.
- Зафиксировать negative test: UUID другого проекта.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-017-POS`: Policy покрывает owner/editor/viewer и child IDs без утечки чужих проектов.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-017-NEG`: UUID другого проекта.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Policy покрывает owner/editor/viewer и child IDs без утечки чужих проектов. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

UUID другого проекта. Изменение Outcome требует пересмотра зависимых карточек.

## Mini-plan — 2026-10-31

BE-015/016 merged (PR #13/#14); BE-017 ready → in_progress: выполнен разбор границ.
Policy принадлежит modules/access, согласно docs/03_MODULE_BOUNDARIES.md; identity даёт
только Principal и не импортирует projects. Точный новый source: modules/access/policy.py,
tests/unit/test_project_policy.py; tests/security включит эту policy suite.
Новых HTTP endpoints/DB tables в BE-017 нет. Интеграция с реальными project/member/node
repositories выполняется BE-019/023/025; до них не заявлять runtime object ACL.

Сначала тестовая матрица owner/editor/viewer/nonmember: read/edit/owner-only, невидимый
проект404, видимый с запрещённой операцией403, owner immutable и owner не может leave,
удалённый project виден только owner для read/restore. Затем cross-project child UUID,
подмена membership user ID, owner precedence над membership, requester/self policies.
Typed ProjectAccessContext передаётся из trusted repository текущего UoW; policy проверяет
actor/context/project/child совпадение и не доверяет role из transport. Использовать
чёткие permission types и явные error codes; без FastAPI/SQLAlchemy imports в policy.
Реализация и её tests ещё не начаты; этот план не является доказательством working ACL.
