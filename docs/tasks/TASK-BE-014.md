---
id: "BE-014"
title: "Модель users, безопасная регистрация, хеширование паролей"
epic: "EPIC-02"
priority: "P0"
status: "planned"
depends_on: ["BE-011", "BE-012", "BE-013"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-AUTH-001", "FR-ACL-001"]
api: ["POST /api/v1/auth/register"]
database: ["auth_sessions", "rate_limit_buckets", "used_refresh_tokens", "users"]
tests: ["BE-014-POS", "BE-014-NEG", "UNIT-API-003", "API-003", "INT-API-003", "SEC-API-003"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-014 — Модель users, безопасная регистрация, хеширование паролей

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Модель users, безопасная регистрация, хеширование паролей. Требования: FR-AUTH-001, FR-ACL-001. Цель — следующий проверяемый инкремент milestone M1.

## Outcome

Register нормализует email, хранит scrypt hash; duplicate/email-invalid не создают account.

## Preconditions

Зависимости: BE-011, BE-012, BE-013. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/modules/identity/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: POST /api/v1/auth/register
Таблицы API: auth_sessions, rate_limit_buckets, used_refresh_tokens, users
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Register нормализует email, хранит scrypt hash; duplicate/email-invalid не создают account.
- Зафиксировать negative test: Email case collision, слабый пароль.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-014-POS`: Register нормализует email, хранит scrypt hash; duplicate/email-invalid не создают account.
Endpoint tests: UNIT-API-003, API-003, INT-API-003, SEC-API-003
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-014-NEG`: Email case collision, слабый пароль.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Register нормализует email, хранит scrypt hash; duplicate/email-invalid не создают account. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Email case collision, слабый пароль. Изменение Outcome требует пересмотра зависимых карточек.
