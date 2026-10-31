# FORMA

Backend научного редактора: LaTeX, PDF, редактируемый DOCX, ZIP. M0 принят и слит; идёт **фаза B**. Реализованы database foundation и health API. Сохранены:
проектная документация и проверяемые контракты; бизнес-методы пока planned.

[Документация](docs/README.md) · [Architectural Review](docs/ARCHITECTURAL_REVIEW.md) ·
[API: 46 методов](docs/09_API_ENDPOINT_CATALOG.md) · [PostgreSQL](docs/05_DATA_MODEL.md) ·
[Карта 52 задач](docs/tasks/ROADMAP.md) · [Фактические проверки](docs/evidence/phase-a.md).

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30. Связи: BE-001–007.

## Проверить фазу A

Требуются Python 3.12, pip, Make; для SQL — PostgreSQL 14+ utilities initdb/pg_ctl/createdb
в PATH (не запускать initdb от root). Скрипт создаёт и удаляет только свой временный кластер.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements-dev.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps .
make ci-local
```

| Существующая команда | Что проверяет |
|---|---|
| make contracts | Перегенерирует OpenAPI, API docs и примеры из DTO/registry |
| make lint | Ruff format/check для contracts/scripts/tests |
| make typecheck | Strict MyPy для src/ и Pydantic DTO |
| make test | Проверки контрактов, examples, ссылок и DAG |
| make openapi-check | Полная suite спецификации |
| make schema-check | DDL, fixtures всех таблиц, отрицательные integrity сценарии |
| make ci-local | Все перечисленные проверки без регенерации исходных contracts |

В CI SQL проверка использует отдельную пустую БД `forma_contract_test` через
`FORMA_TEST_DATABASE_URL`. Другие имена и непустая БД отвергаются. Никогда не передавать
пользовательскую БД в эту переменную.

make dev-up, make migrate и make test-integration доступны. make test-security доступен для существующих config/logging/HTTP controls. Наличие schema.sql не означает выполненную миграцию.
Не использовать `docker compose down -v` для устранения неполадок.

BE-008 добавляет устанавливаемый typed package forma_backend; `make lock-check` проверяет версии среды против lock. App factory доступна в BE-012.

BE-010: load_settings() валидирует окружение, не загружает .env автоматически. Заменить CHANGE_ME secrets; production требует HTTPS origins и Secure cookie. Логи forma используют whitelist и ContextVar request IDs; HTTP middleware реализован в BE-012.

## BE-009: локальный PostgreSQL и образ

Docker Engine + Compose v2 обязательны. `cp .env.example .env`, заменить POSTGRES_PASSWORD
и остальные CHANGE_ME значения. `make dev-up` запускает PostgreSQL без host port;
`make dev-down` останавливает проект, сохраняя тома. Для host SQL tools явно добавить
`-f infra/compose.dev.yaml` к Compose command; порт слушает только 127.0.0.1.
Python image собирается `docker compose --env-file .env -f infra/compose.yaml build backend`.
Одноразовый tools service проверяет импорт package от UID10001; это ещё не API/worker.
Их runtime-интеграция — BE-012/032 по ADR-0008.

`make test-compose` создаёт отдельный случайно названный тестовый проект, проверяет
PostgreSQL health, non-root image и DB/files persistence при recreate. Затем удаляет
только контейнеры/тома своего тестового проекта по уникальной Compose label.
Пользовательский проект forma не используется. `down -v` не применяется.

## BE-011: database foundation

make migrate применяет Alembic upgrade head, make migration-check проверяет drift
реализованного ORM-среза. Требуется DATABASE_URL в окружении, .env автоматически не читается.
make test-integration проверяет реальные миграции в отдельной БД: локально поднимает
свой временный PostgreSQL container, в CI создаёт UUID-named test DB на выделенном сервере.
Приложение/пользовательские volumes не используются. Runtime migrations сейчас создают
только четыре identity таблицы; полный design schema.sql из 14 таблиц остаётся целевой схемой.
Unit of Work откатывает всё без явного commit(), SQL/параметры не логируются.

## BE-012: health API

После настройки .env: make dev-up собирает image и поднимает PostgreSQL/API с healthchecks;
API слушает localhost:8000 через dev override. GET /health/live не требует БД;
GET /health/ready проверяет DB+storage и возвращает503 при недоступности/дедлайне2s.
Swagger /docs и /openapi.json доступны только вне production; runtime содержит два health
метода, остальные44 остаются в planned контракте. Запуск без Docker: передать окружение
и выполнить .venv/bin/python -m uvicorn forma_backend.main:create_app --factory --no-access-log.
Запускать migrations отдельно до product API; health probe сам схему не создаёт.

## BE-013: CI gates

CI содержит восемь реальных checks: lint, types, unit-tests, integration-tests,
migration-check, security-tests, docker-build, docs-contract. make test-migrations —
DB revision/drift suite; make test-security — текущие config/HTTP/logging security tests;
make dependency-check — pip check, совместимость installed dependency graph (не CVE scan).
make ci-local + make test-compose воспроизводят проверки; main/PR используют один workflow.

## BE-014: регистрация

После make migrate доступен POST /api/v1/auth/register: email/password/display_name → Profile201.
Email strip/lower; пароль12–128 символов, scrypt с random salt; duplicate409 EMAIL_TAKEN.
Сессия не создаётся. JSON≤2MiB, register IP quota10/15min и bounded hashing.
Runtime содержит3 метода; login/refresh ещё planned. make test-security теперь включает
password hashing и registration boundary; PostgreSQL integration проверяет реальные races.

## BE-015: сессии

POST /api/v1/auth/login возвращает access/CSRF JSON и устанавливает refresh cookie.
POST refresh/logout: credentials include + Origin + X-CSRF-Token; login требует Origin.
Bearer нужен для logout-all, GET sessions и DELETE sessions/{session_id}. Cookies — HttpOnly,
Secure по окружению, SameSite Strict, Path=/api/v1/auth. Reload без CSRF требует login.
JWT key rotation — JWT_KEY_ID и optional previous key pair; не хранить значения в Git.
После нового lock выполнить install по README и переустановить пакет. make test-security
включает real PostgreSQL auth tests (локально Docker), а Docker smoke проверяет register→login→refresh→sessions.
Runtime9 методов, profile/change-password остаются следующей задачей BE-016.

BE-016: GET/PATCH `/api/v1/users/me`, POST `/api/v1/users/me/change-password` implemented.
Изменяется только display_name; новый password12..128. Смена требует current_password
и отзывает все сессии включая текущую (204, cookie очищается). После неё нужен login.

BE-017: чистая политика project ACL в `modules/access/policy.py`: owner/editor/viewer,
project/object UUID scope, owner-only/self/requester и deleted visibility. Проверены unit/security
scenarios. Подключение к реальным project repositories/routes — последующие задачи;
runtime API по-прежнему12 implemented /34 planned.

BE-018: auth limits проверены под конкурентной нагрузкой и на границе fixed window;
долгая transaction использует текущее DB statement time. `make auth-limits-cleanup`
удаляет bounded batch rate buckets старше24h из настроенной БД, без удаления пользовательских томов.
CLI доступен в packaged image; автоматический scheduler ещё planned.

BE-024: typed UUID FileStorage + POSIX local adapter и PostgreSQL shared/exclusive barrier.
Проверяются private single-link files, capacity floors, atomic reserved rename, guarded metadata
commit и безопасный GC. API/DB integration — BE-019/025, backup/retention scheduler — BE-047.
