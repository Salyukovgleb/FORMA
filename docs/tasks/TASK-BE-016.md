---
id: "BE-016"
title: "Profile read/update и смена пароля"
epic: "EPIC-02"
priority: "P0"
status: "planned"
depends_on: ["BE-015"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-AUTH-001", "FR-ACL-001"]
api: ["GET /api/v1/users/me", "PATCH /api/v1/users/me", "POST /api/v1/users/me/change-password"]
database: ["auth_sessions", "rate_limit_buckets", "used_refresh_tokens", "users"]
tests: ["BE-016-POS", "BE-016-NEG", "UNIT-API-008", "API-008", "INT-API-008", "SEC-API-008", "UNIT-API-009", "API-009", "INT-API-009", "SEC-API-009", "UNIT-API-010", "API-010", "INT-API-010", "SEC-API-010"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-016 — Profile read/update и смена пароля

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Profile read/update и смена пароля. Требования: FR-AUTH-001, FR-ACL-001. Цель — следующий проверяемый инкремент milestone M1.

## Outcome

Profile update ограничен display_name; password change отзывает все сессии.

## Preconditions

Зависимости: BE-015. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/modules/identity/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: GET /api/v1/users/me, PATCH /api/v1/users/me, POST /api/v1/users/me/change-password
Таблицы API: auth_sessions, rate_limit_buckets, used_refresh_tokens, users
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Profile update ограничен display_name; password change отзывает все сессии.
- Зафиксировать negative test: Чужой профиль и неверный current_password.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-016-POS`: Profile update ограничен display_name; password change отзывает все сессии.
Endpoint tests: UNIT-API-008, API-008, INT-API-008, SEC-API-008, UNIT-API-009, API-009, INT-API-009, SEC-API-009, UNIT-API-010, API-010, INT-API-010, SEC-API-010
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-016-NEG`: Чужой профиль и неверный current_password.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Profile update ограничен display_name; password change отзывает все сессии. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Чужой профиль и неверный current_password. Изменение Outcome требует пересмотра зависимых карточек.
