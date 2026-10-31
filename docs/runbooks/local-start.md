# Runbook: local-start

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](../tasks/ROADMAP.md).

Prerequisites фазы A: Python3.12, pip, PostgreSQL client/server utilities для local SQL check.
Выполнить `python3.12 -m venv .venv`, `.venv/bin/python -m pip install --require-hashes -r requirements-dev.lock`,
`make ci-local`. Expected: contracts/schema tests pass. Runtime Compose ещё planned в BE-009;
не обещать доступный :8000. После реализации проверить Docker volume persistence отдельным
recreate smoke без удаления томов; production sandbox требует Linux, rootless cgroups.

## Docker bootstrap (2026-10-31)

Убедиться docker info/compose version работают. Скопировать .env.example в .env,
заменить POSTGRES_PASSWORD, затем make dev-up. Ожидать healthy postgres.
make dev-down сохраняет volumes. make test-compose использует отдельный случайный
проект, проверяет persistence и очищает только свои тестовые volumes.
Если порт5432 занят, base Compose не публикует его; dev override добавлять явно.

## Auth rate bucket cleanup (BE-018)

При уже экспортированном environment API: `make auth-limits-cleanup` (до1000 expired rows).
В работающем Compose: `docker compose --env-file .env -f infra/compose.yaml exec -T api python -m forma_backend.infrastructure.identity.cleanup_limits --max-rows 1000`.
При необходимости повторять до removed=0, затем повторить после окончания активных transactions:
SKIP LOCKED может оставить locked rows. Удаляются только buckets старше24h; API credentials
и current quotas не сбрасываются. Команда не удаляет volumes или auth sessions/history.
Exit0 — committed batch; exit1 — configuration/DB/timeout failure и rollback; exit2 — invalid batch size.
Если timeout повторяется на крупной таблице, не убирать timeouts автоматически: изучить EXPLAIN
и expiry index в BE-048. Внешний schedule ещё не настроен, назначить operator cadence до release.

## Storage adapter prerequisites (BE-024)

POSIX (production Linux image); root должен существовать и принадлежать service UID, без
symlink в компонентах пути и без group/world write. Storage root обслуживает ровно одну
backend DB authority; не использовать один volume с независимыми БД и разными locks.
revisions/artifacts/temp создаются0700; generated files0600. Не исправлять проблему chmod777.
Capacity defaults: available≥2GiB и≥10%; отказ даёт StorageUnavailable, не удаляет пользовательские данные.
Весь publish/read/GC вызывается под MaintenanceGuard; metadata — только через ту же connection
и explicit lease.commit(). ORM Session.commit не должен завершать outer guarded transaction.
DB lost/uncertain commit: проверить DB state перед retry, не чистить свежий blob сразу.
Manual GC discovery/retention и backup scripts ещё BE-047, публичный storage API ещё BE-019/025.
