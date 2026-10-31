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
