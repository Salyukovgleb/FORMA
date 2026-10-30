# FORMA

Backend научного редактора: LaTeX, PDF, редактируемый DOCX, ZIP. Сейчас **фаза A**:
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
make ci-local
```

| Существующая команда | Что проверяет |
|---|---|
| make contracts | Перегенерирует OpenAPI, API docs и примеры из DTO/registry |
| make lint | Ruff format/check для contracts/scripts/tests |
| make typecheck | Strict MyPy для всех Pydantic DTO; application src ещё нет |
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
