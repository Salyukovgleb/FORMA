---
id: "BE-012"
title: "FastAPI app factory, единые ошибки, health/ready, OpenAPI"
epic: "EPIC-01"
priority: "P0"
status: "planned"
depends_on: ["BE-010", "BE-011"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["NFR-OPS-001"]
api: ["GET /health/live", "GET /health/ready"]
database: []
tests: ["BE-012-POS", "BE-012-NEG", "UNIT-API-001", "API-001", "INT-API-001", "SEC-API-001", "UNIT-API-002", "API-002", "INT-API-002", "SEC-API-002"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-012 — FastAPI app factory, единые ошибки, health/ready, OpenAPI

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

FastAPI app factory, единые ошибки, health/ready, OpenAPI. Требования: NFR-OPS-001. Цель — следующий проверяемый инкремент milestone M0.

## Outcome

App factory выдаёт health, единый error envelope и runtime OpenAPI.

## Preconditions

Зависимости: BE-010, BE-011. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/core/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: GET /health/live, GET /health/ready
Таблицы API: Схема/инфраструктурный impact определяется Outcome; целевой DDL в database/schema.sql.
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: App factory выдаёт health, единый error envelope и runtime OpenAPI.
- Зафиксировать negative test: DB down даёт ready503, live200.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-012-POS`: App factory выдаёт health, единый error envelope и runtime OpenAPI.
Endpoint tests: UNIT-API-001, API-001, INT-API-001, SEC-API-001, UNIT-API-002, API-002, INT-API-002, SEC-API-002
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-012-NEG`: DB down даёт ready503, live200.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

App factory выдаёт health, единый error envelope и runtime OpenAPI. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

DB down даёт ready503, live200. Изменение Outcome требует пересмотра зависимых карточек.

ADR-0008 integration gate: Добавить Compose API service и smoke health/ready на действующем PostgreSQL.
