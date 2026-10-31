# Changelog

Владелец: backend-developer. Статус: draft. Обновлено: 2026-10-30. Связи: BE-001–007.

## Unreleased

- Проектная документация фазы A: архитектура, ADR, PostgreSQL, API, задачи и runbooks.
- Исполняемые Pydantic DTO, OpenAPI generator и validation tooling.
- Продуктовые API, миграции и pipeline документов пока planned.

- M0 принят пользователем и merged через PR #1.
- BE-008: устанавливаемый typed Python package, lock verification, isolated import tests.

- BE-010: validated environment, protected secret representation, JSON event logging and isolated correlation context.

- BE-009: digest-pinned non-root image, PostgreSQL/volume bootstrap, real persistence smoke and Docker CI.

- BE-011: typed identity persistence, explicit transactions, guarded Alembic revisions and real PostgreSQL migration tests.

- BE-012: FastAPI factory, safe error/correlation boundary, health/readiness, dev Swagger, explicit CORS and live API Compose smoke.

- BE-013: eight CI gates, shared locked setup, quality-policy guard and dependency graph validation.

- BE-014: registration, bounded salted scrypt, atomic uniqueness/IP limit and protected request body handling.

- BE-015: JWT access with DB revocation, hashed rotating refresh/CSRF, own-session management and key rotation.

- BE-016: own profile read/update, bounded password change, atomic revoke-all and login/change serialization; shared wire models and Docker profile smoke.
