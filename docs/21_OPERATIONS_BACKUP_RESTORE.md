# Backup и восстановление

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

MVP backup с краткой остановкой writes и GC: включить maintenance (503 для mutations),
остановить enqueue, дождаться terminal jobs или отменить/kill; взять exclusive maintenance
advisory lock (тот же протокол, что publishers). Остановить API/worker writers; PostgreSQL
остаётся доступен backup connection. Выполнить pg_dump custom format + копию revisions/artifacts
и SHA256 manifest, сохранить версии приложения/schema/image и время. Пока lock удерживается,
никаких publishers/GC. Проверить dump exit status и manifest, затем снять maintenance.
Не заявлять consistency между произвольным pg_dump и live rsync без этого барьера.

Расписание: ежедневно 02:00 Europe/Minsk, хранить 7 daily + 4 weekly. Destination отдельный
диск/хост, encrypted at rest, permissions 0700; автоматическая upload внешнему сервису не нужна.
RPO≤24h, RTO≤4h для ≤20 GiB данных — целевые, требуют BE-047 измерения.
Restore ежемесячно в изолированные DB/volume: pg_restore → files → SQL FK проверки →
пересчитать hashes всех referenced keys → auth revoke all → smoke compile/download →
сопоставить counts. Не восстанавливать поверх работающего volume. Cutover после review отчёта.

Purge deleted projects после 7 суток: maintenance shared lock + lock project; terminal jobs
и отсутствие live attempts; удалить jobs/artifacts/logs, snapshots/entries, main_file_id=null,
nodes/revisions, members, project; audit project_id set null. Commit, затем GC orphan blobs.
History revisions 30 суток, current/pinned не удалять; project purge освобождает snapshot pins.
Восстановление отдельного удалённого файла не API MVP; доступно оператору через backup,
без обещания восстановления после retention.
