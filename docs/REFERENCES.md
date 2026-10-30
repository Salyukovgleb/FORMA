# Технические источники

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

Официальные источники, просмотрены 2026-10-30:

- [PostgreSQL SELECT / SKIP LOCKED](https://www.postgresql.org/docs/14/sql-select.html): queue consumers могут пропускать locked rows; это не общий consistent read.
- [Docker run flags](https://docs.docker.com/reference/cli/docker/container/run): network/read-only/tmpfs/PID/security options; реальность ограничения проверяется на host.
- [Docker Engine security](https://docs.docker.com/engine/security/): daemon — часть trusted computing base; socket не выдаётся parser.
- [Pydantic JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/): model_json_schema используется для contract artifacts.

Выбор протоколов fencing/backup/ACL — проектные решения FORMA, не гарантия этих библиотек.
