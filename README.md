# FORMA

Backend научного редактора: LaTeX, PDF, редактируемый DOCX, ZIP. M0 принят и слит; начата **фаза B, BE-008**. Сохранены:
проектная документация и проверяемые контракты; продуктовый сервер ещё не реализован.

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

make dev-up/migrate/test-integration/test-security пока отсутствуют: они будут добавлены
с реальным приложением в BE-009/011/013. Наличие schema.sql не означает выполненную миграцию.
Не использовать `docker compose down -v` для устранения неполадок.

BE-008 добавляет устанавливаемый typed package forma_backend; `make lock-check` проверяет версии среды против lock. HTTP application пока отсутствует.

BE-010: load_settings() валидирует окружение, не загружает .env автоматически. Заменить CHANGE_ME secrets; production требует HTTPS origins и Secure cookie. Логи forma используют whitelist и ContextVar request IDs; HTTP middleware ещё planned.

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
