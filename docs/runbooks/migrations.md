# Runbook: migrations

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](../tasks/ROADMAP.md).

BE-011 создаст Alembic environment. До этого schema.sql проверяется только в disposable DB:
`make schema-check`. Product migration procedure: maintenance/backup → проверить revision →
единственный migrator `alembic upgrade head` → `alembic check` → smoke → открыть writes.
При ошибке сохранить logs/revision, не запускать downgrade на user data. В тестах fresh и seeded
upgrade обязательны; exact commands появятся вместе с Alembic, сейчас они planned.

## BE-011 commands

Установить обновлённый lock и пакет согласно README. Задать DATABASE_URL в окружении
процесса (postgresql+psycopg URL, без вывода секрета в журнал), затем make migrate,
make migration-check. .env автоматически не читается. Для host CLI использовать
localhost PostgreSQL из compose.dev.yaml; внутри Docker сеть видит postgres hostname.
В образе миграции находятся /opt/forma/alembic.ini; вызвать python -m alembic
-c /opt/forma/alembic.ini upgrade head с переданным DATABASE_URL.
make test-integration сам создаёт disposable DB и не мигрирует пользовательскую БД.
