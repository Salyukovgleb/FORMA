# Локальное развёртывание

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

План BE-009: Compose services postgres, api, worker-controller; persistent pgdata и files,
readiness и startup ordering. API bind localhost:8000 в dev; Postgres без public host port
в production. Все runtime processes non-root, secrets через environment вне Git.
API/worker один Python dependency lock, compiler image отдельно pinned TeX Live/Pandoc/fonts.
Production worker-controller rootless Docker socket; API не монтирует socket. Rootless daemon
и cgroup delegation — host prerequisite, не скрытый дополнительный облачный сервис.
Compose dev использует локальный Docker daemon только для разработки; desktop validation
не является production security evidence. Production target Linux описан ADR-0004.

Целевая структура после foundation: src/forma_backend/{core,shared,modules,infrastructure},
alembic/, tests/{unit,integration,api,workers,security,fixtures}, infra/docker/,
infra/compose.yaml, infra/compose.dev.yaml. Сейчас эти пустые каталоги и фиктивное приложение
не создаются. Точные существующие команды фазы A — в корневом README и Makefile.
Будущие make dev-up/migrate/test-integration/test-security появятся в BE-009/011/013;
сейчас запускать их нельзя. Никогда не применять docker compose down -v к пользовательским данным.

## BE-009: bootstrap implemented

infra/compose.yaml запускает PostgreSQL16.6 (digest pinned) с persistent pgdata.
Python3.12 image (digest pinned) multi-stage, runtime UID10001, tools profile с files volume,
read-only rootfs, cap-drop ALL и no-new-privileges. Это не sandbox для документов.
Dev override публикует только localhost SQL port; production base без host ports.
Существующие команды теперь make dev-up, make dev-down, make test-compose; make migrate
появится в BE-011. Dockerfile использует отдельные hashed runtime/build locks.
API/worker services появятся в BE-012/032 согласно ADR-0008.
