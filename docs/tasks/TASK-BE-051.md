---
id: "BE-051"
title: "Clean install из README, миграции, пример проекта, PDF/DOCX E2E"
epic: "EPIC-07"
priority: "P0"
status: "planned"
depends_on: ["BE-013", "BE-021", "BE-045", "BE-047", "BE-048", "BE-050"]
owner: "backend-developer"
estimate: "2–4 developer days"
requirements: ["NFR-OPS-001", "NFR-SEC-001"]
api: []
database: []
tests: ["BE-051-POS", "BE-051-NEG"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-051 — Clean install из README, миграции, пример проекта, PDF/DOCX E2E

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Clean install из README, миграции, пример проекта, PDF/DOCX E2E. Требования: NFR-OPS-001, NFR-SEC-001. Цель — следующий проверяемый инкремент milestone M6.

## Outcome

Чистая Linux машина проходит README→migrations→PDF/DOCX/ZIP→restore.

## Preconditions

Зависимости: BE-013, BE-021, BE-045, BE-047, BE-048, BE-050. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/infrastructure/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: Публичный endpoint не добавляется этой задачей.
Таблицы API: Схема/инфраструктурный impact определяется Outcome; целевой DDL в database/schema.sql.
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Чистая Linux машина проходит README→migrations→PDF/DOCX/ZIP→restore.
- Зафиксировать negative test: Missing host cgroup delegation.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-051-POS`: Чистая Linux машина проходит README→migrations→PDF/DOCX/ZIP→restore.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-051-NEG`: Missing host cgroup delegation.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Чистая Linux машина проходит README→migrations→PDF/DOCX/ZIP→restore. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Missing host cgroup delegation. Изменение Outcome требует пересмотра зависимых карточек.

ADR-0008 integration gate: Проверить совместный clean-room Compose запуск API/Postgres/worker и persistence.
