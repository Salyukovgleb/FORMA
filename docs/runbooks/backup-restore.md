# Runbook: backup-restore

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](../tasks/ROADMAP.md).

Следовать [протоколу](../21_OPERATIONS_BACKUP_RESTORE.md). До backup остановить writers/GC
и удерживать maintenance barrier. Команды оператора после BE-047: `pg_dump -Fc` в отдельный
backup directory, копия referenced revisions/artifacts + SHA256 manifest; exit code проверяется.
Restore только в новый target: `createdb`, `pg_restore --exit-on-error`, восстановление files,
проверка всех DB references/hash, revoke sessions, smoke. Имена DB/paths берутся из inventory,
не подставлять production по умолчанию. Interrupted backup помечается incomplete и не участвует
в rotation. Удалять старые backup только после успешного нового и контрольного restore.
