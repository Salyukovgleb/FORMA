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
