---
id: "BE-010"
title: "Конфигурация окружений, secrets, logging, correlation IDs"
epic: "EPIC-01"
priority: "P0"
status: "done"
depends_on: ["BE-008"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["NFR-OPS-001"]
api: []
database: []
tests: ["BE-010-POS", "BE-010-NEG"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-010 — Конфигурация окружений, secrets, logging, correlation IDs

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Конфигурация окружений, secrets, logging, correlation IDs. Требования: NFR-OPS-001. Цель — следующий проверяемый инкремент milestone M1.

## Outcome

Невалидная prod config отвергается; request ID проходит через структурированные логи без secrets.

## Preconditions

Зависимости: BE-008. Для реализации они должны быть done;
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

- Написать positive test: Невалидная prod config отвергается; request ID проходит через структурированные логи без secrets.
- Зафиксировать negative test: Prod с пустым secret не стартует.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-010-POS`: Невалидная prod config отвергается; request ID проходит через структурированные логи без secrets.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-010-NEG`: Prod с пустым secret не стартует.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Невалидная prod config отвергается; request ID проходит через структурированные логи без secrets. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Prod с пустым secret не стартует. Изменение Outcome требует пересмотра зависимых карточек.

## Mini-plan / evidence

BE-008 merged. Добавлены core/config.py (typed environment validation, SecretStr,
redacted startup errors) и core/logging.py (allowlisted JSON events, ContextVar IDs).
Тесты сначала упали на отсутствующем core; после реализации `make ci-local`: 26 passed,
Ruff, strict MyPy (5 files), lock и design PostgreSQL checks green.
HTTP middleware будет в BE-012; raw сообщения/exception text намеренно не логируются.
API/DB contract не меняется. Дополнительных runtime libraries кроме уже принятого Pydantic нет.

2026-10-31: подтверждён merge PR #3, `7aad6c1`; head `23ac085`, CI run 41084839338 SUCCESS. Повторный локальный make ci-local: 26 passed, Ruff/MyPy/lock/schema green.
