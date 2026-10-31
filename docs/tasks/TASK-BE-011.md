---
id: "BE-011"
title: "SQLAlchemy/Alembic и первая миграция + smoke-test"
epic: "EPIC-01"
priority: "P0"
status: "ready"
depends_on: ["BE-009"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["NFR-OPS-001"]
api: []
database: []
tests: ["BE-011-POS", "BE-011-NEG"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-011 — SQLAlchemy/Alembic и первая миграция + smoke-test

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

SQLAlchemy/Alembic и первая миграция + smoke-test. Требования: NFR-OPS-001. Цель — следующий проверяемый инкремент milestone M0.

## Outcome

Alembic fresh и seeded upgrade работают; schema drift обнаруживается.

## Preconditions

Зависимости: BE-009. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/core/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: Публичный endpoint не добавляется этой задачей.
Таблицы API: Схема/инфраструктурный impact определяется Outcome; целевой DDL в database/schema.sql.
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Alembic fresh и seeded upgrade работают; schema drift обнаруживается.
- Зафиксировать negative test: Upgrade с существующими rows не теряет данные.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-011-POS`: Alembic fresh и seeded upgrade работают; schema drift обнаруживается.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-011-NEG`: Upgrade с существующими rows не теряет данные.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Alembic fresh и seeded upgrade работают; schema drift обнаруживается. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Upgrade с существующими rows не теряет данные. Изменение Outcome требует пересмотра зависимых карточек.
