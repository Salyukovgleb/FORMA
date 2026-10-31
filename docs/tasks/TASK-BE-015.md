---
id: "BE-015"
title: "Login, refresh rotation, logout, session revocation"
epic: "EPIC-02"
priority: "P0"
status: "in_review"
depends_on: ["BE-014"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-AUTH-001", "FR-ACL-001"]
api: ["POST /api/v1/auth/login", "POST /api/v1/auth/refresh", "POST /api/v1/auth/logout", "POST /api/v1/auth/logout-all", "GET /api/v1/auth/sessions", "DELETE /api/v1/auth/sessions/{session_id}"]
database: ["auth_sessions", "rate_limit_buckets", "used_refresh_tokens", "users"]
tests: ["BE-015-POS", "BE-015-NEG", "UNIT-API-004", "API-004", "INT-API-004", "SEC-API-004", "UNIT-API-005", "API-005", "INT-API-005", "SEC-API-005", "UNIT-API-006", "API-006", "INT-API-006", "SEC-API-006", "UNIT-API-007", "API-007", "INT-API-007", "SEC-API-007", "UNIT-API-011", "API-011", "INT-API-011", "SEC-API-011", "UNIT-API-012", "API-012", "INT-API-012", "SEC-API-012"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-015 — Login, refresh rotation, logout, session revocation

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Login, refresh rotation, logout, session revocation. Требования: FR-AUTH-001, FR-ACL-001. Цель — следующий проверяемый инкремент milestone M2.

## Outcome

Login, rotation, sessions list/revoke и replay protection дают немедленный отзыв JWT.

## Preconditions

Зависимости: BE-014. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/modules/identity/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: POST /api/v1/auth/login, POST /api/v1/auth/refresh, POST /api/v1/auth/logout, POST /api/v1/auth/logout-all, GET /api/v1/auth/sessions, DELETE /api/v1/auth/sessions/{session_id}
Таблицы API: auth_sessions, rate_limit_buckets, used_refresh_tokens, users
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Login, rotation, sessions list/revoke и replay protection дают немедленный отзыв JWT.
- Зафиксировать negative test: Двойной refresh и replay старого token.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-015-POS`: Login, rotation, sessions list/revoke и replay protection дают немедленный отзыв JWT.
Endpoint tests: UNIT-API-004, API-004, INT-API-004, SEC-API-004, UNIT-API-005, API-005, INT-API-005, SEC-API-005, UNIT-API-006, API-006, INT-API-006, SEC-API-006, UNIT-API-007, API-007, INT-API-007, SEC-API-007, UNIT-API-011, API-011, INT-API-011, SEC-API-011, UNIT-API-012, API-012, INT-API-012, SEC-API-012
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-015-NEG`: Двойной refresh и replay старого token.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Login, rotation, sessions list/revoke и replay protection дают немедленный отзыв JWT. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Двойной refresh и replay старого token. Изменение Outcome требует пересмотра зависимых карточек.

## Mini-plan / implementation evidence — 2026-10-31

BE-014 merged. Application session use cases работают с transaction store/crypto ports;
SQLAlchemy и PyJWT adapters — infrastructure. Login блокирует user до проверки/создания session.
Refresh сначала находит ID по current/history hash, затем locks по ID; replay revoke commit
выполняется до исключения, поэтому повтор не откатывает security effect. Concurrency barrier
принудительно проверяет два lookup до claim. Ключи JWT локальные; HS256 fixed, mandatory
claims/UUID/time bounds, active/previous kid. Каждый access проверяет active user + session в DB.

Cookie HttpOnly/Secure/SameSite Strict/Path auth; refresh/login/logout проверяют Origin,
refresh/logout требуют CSRF header. History/hash only, absolute TTL30d без sliding;
access600s. Login unknown user выполняет dummy scrypt, error одинаковый. List/revoke only own,
keyset cursor привязан к user filter. Logout idempotent, logout-all немедленно отзывает JWT.
Public limits login IP/email10/15min; refresh session30/min в той же transaction (без второго
DB connection под session lock). Cleanup и полная auth review — BE-018.

Тесты написаны до handlers (login404), затем real PostgreSQL scenarios, malformed JWT,
key rotation, cookie/CSRF, expiry/disabled user, foreign sessions, replay race, hash-only
storage, no secret logs, pagination/revoke и absolute expiry. Docker выполняет весь auth smoke.
Новых migrations нет; используется схема BE-011. Profile/change-password — BE-016, не здесь.
