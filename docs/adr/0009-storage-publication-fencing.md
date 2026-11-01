# ADR-0009: publication reservation and guarded metadata connection

Владелец: backend-developer. Статус: implemented (technical self-review). Обновлено: 2026-10-31.
Связи: BE-024, ADR-0002, docs/11_LOCAL_FILE_STORAGE.md.

## Контекст

POSIX rename заменяет существующий destination. UUID generated server-side всё равно должен
защищаться от collision. PostgreSQL advisory lock освобождается при потере session; отдельная
metadata connection могла бы затем ошибочно commit без barrier. Atomic transaction между
PostgreSQL и filesystem отсутствует; мгновенное прекращение filesystem syscall при сетевой
потере DB connection гарантировать невозможно.

## Решение

Dedicated connection держит session-level shared/exclusive advisory lock (two-int key
1179603533/1, FORМ namespace). Та же connection используется будущим metadata UoW; explicit
lease.commit() проверяет backend PID и наличие lock перед commit. Connection loss sticky:
lease не reconnect/reacquire и не предоставляет новую connection для продолжения операции.
Не более8 detached guards на process (nonblocking semaphore, busy503).
Connection.detach() исключает session из pool; даже ранний close физически освобождает lock.
Teardown rollback/unlock;
при ошибке original DBAPI handle явно close, затем SQLAlchemy connection invalidated.
Один invalidate detached proxy недостаточен: original handle удерживается и закрывается явно. GC/backup получают exclusive, publishers/downloads shared.
Nonblocking acquisition возвращает typed busy error вместо неограниченного ожидания.

Publication: generated UUID, private temp O_EXCL → bounded write → fsync file → guard check →
reserve destination O_EXCL → verify reservation/stage inode → same-filesystem rename поверх
только собственной reservation → fsync обеих directories → guard check. Existing blob никогда
не резервируется/не overwrite. fd-relative no-follow traversal, owned non-writable-by-others
directories, regular private single-link files; unknown paths из клиента не принимаются.

После обнаружения lost connection дальнейшие publish/commit запрещены. Loss между check и
rename может оставить новый orphan; после обнаруженного loss новый commit не отправляется
и metadata не переносится на replacement connection. GC удаляет только blobs >24h с authoritative reference probe
под exclusive guard; новые orphans не собираются немедленно. Это уточняет прежнее буквальное
«не завершать rename после потери lock»: safety invariant — durable bytes до metadata commit, запрет replacement-connection commit
после обнаруженного loss, bounded filesystem effects, а не атомарность двух систем.
Loss во время уже отправленного COMMIT может дать uncertain outcome: нельзя считать error
доказательством rollback. Authoritative GC reference probe защищает уже committed metadata.

Storage root доступен только service UID/оператору. Защита покрывает untrusted keys,
symlink/hardlink и descriptor-relative races; hostile процесс того же UID/root, меняющий уже
открытые файлы, относится к compromised host и не изолируется filesystem adapter.

## Последствия / проверка

Нет новых services/dependencies/DB tables. FileStorage не делает DB commits; caller управляет
UoW через guarded connection и lease.commit(). Нельзя commit ORM Session независимо от lease.
Reference probe GC — trusted repository, не transport boolean. DB references/retention
integration — BE-019/025/047; здесь adapter и barrier tests на disposable DB/temp roots.

Tests: collision, short/zero write, ENOSPC/fsync/rename failure, crashed publisher/orphan,
failed metadata transaction, connection termination/unlock, shared/exclusive across sessions,
reference/age GC и malicious filesystem entries. Linux CI проверяет target POSIX runtime.

Источники: [Python os.rename](https://docs.python.org/3.12/library/os.html#os.rename),
[PostgreSQL advisory locks](https://www.postgresql.org/docs/16/explicit-locking.html#ADVISORY-LOCKS).

[SQLAlchemy connection lifecycle/detach](https://docs.sqlalchemy.org/en/20/core/connections.html),
[pool reset](https://docs.sqlalchemy.org/en/20/core/pooling.html): rollback alone не очищает session state.

## BE-019 refinement — 2026-11-01

Project UoW pin READ COMMITTED на самой dedicated Connection до первого SQL (параметр
MaintenanceGuard isolation). Inherited Engine execution-options недостаточно считать гарантией;
test проверяет SHOW transaction_isolation и quota race при исходном RR default. Остальные
storage guards сохраняют default isolation; API/public DB schema не меняются этим уточнением.
