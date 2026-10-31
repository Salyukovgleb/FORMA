# Локальное хранение

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

| Каталог | Содержимое | Retention / backup |
|---|---|---|
| projects/ | Зарезервирован для server-generated metadata, не mutable source | Не источник истины; можно восстановить |
| revisions/<uuid> | Immutable bytes каждой версии | Current всегда; остальные 30 суток если не pinned; backup |
| job-inputs/<job>/<attempt>/ | Материализованный snapshot | До завершения attempt + 1 час; восстанавливается из revisions |
| artifacts/<uuid> | Проверенный PDF/DOCX/ZIP | 7 суток; backup |
| temp/<uuid> | Незавершённая публикация | GC после 24 часов; backup не нужен |

Physical paths строятся только из generated UUID. Logical paths NFC, POSIX separators,
case-sensitive; запрещены NUL/control, backslash, slash в имени, dot/dotdot, absolute path,
Windows reserved basename, trailing dot/space. Depth ≤20, path ≤1024 символов, name ≤255.
Открытие через dirfd/no-follow, проверка regular file; symlink/hardlink не принимаются.
Whitelist: .tex/.bib/.sty/.cls/.bst/.txt text/plain; .png image/png; .jpg/.jpeg image/jpeg;
.pdf application/pdf для includegraphics. SVG/EPS/исполняемые файлы/архив uploads запрещены.
Magic/MIME должны соответствовать; text только UTF-8 без NUL. .sty/.cls — всё ещё untrusted code.

Write protocol: удержать shared global maintenance advisory lock на dedicated connection
(она же metadata UoW connection, ADR-0009);
stage → fsync file → rename same filesystem → fsync dir; затем lock owner/project, quota check,
INSERT revision, commit. После обнаружения потери DB connection publisher не продолжает publish/commit и не
reconnect. Loss между check/rename допускает orphan; loss во время COMMIT даёт uncertain outcome. Orphan immutable blobs возможны; DB никогда не ссылается на неопубликованные bytes.
GC берёт exclusive тот же advisory lock, поэтому не пересекается с publisher/backup;
удаляет DB references с учётом snapshots, commit, затем unreferenced blobs older 24h.
GC никогда не удаляет referenced blob. Crash после DB GC до unlink оставляет лишь orphan.

Owner quota 2 GiB всех retained revisions + artifacts; project 500 MiB retained bytes,
2000 live nodes, upload 20 MiB, source text 1 MiB. Проверка quota под lock owner затем project,
без cached counter, SUM по indexed joins для MVP. Диск <10% свободного или <2 GiB → 503
STORAGE_UNAVAILABLE до публикации. Snapshot staging максимум 500 MiB; только один running job
на проект. По умолчанию worker slots=1; общий writable scratch bounded 512 MiB на job.

## BE-024 implemented adapter / barrier

`modules/project_files/storage.py`: BlobKey(area enum, UUID), StoredBlob(size, SHA256),
FileStorage/StorageLease/BlobReferences ports и безопасные exceptions. Никаких logical names
или paths из клиента. `infrastructure/storage/local.py`: publish/open/delete/collect_temp.
Regular private single-link files, owned root/directories без group/world write, каждый
компонент через dirfd/O_NOFOLLOW; inode checks обнаруживают directory replacement.
Root должен существовать; revisions/artifacts/temp создаются0700, files0600. Все на одном filesystem.

Publication использует O_EXCL destination reservation перед rename; existing UUID никогда
не overwrite. File/dirs fsync до возврата StoredBlob. Exceptions оставляют только staging или
immutable orphan; после errors нельзя делать metadata insert. Open не следует symlink,
не блокируется на FIFO и не принимает hardlink. Stream max_bytes20MiB default, максимум100MiB
для artifacts; logical text/MIME/ACL/owner quotas проверят следующие use cases.
Free capacity по fstatvfs:2GiB и10% defaults; fixtures явно меняют capacity floors только
для воспроизводимых I/O tests, отдельно проверены оба production thresholds.

MaintenanceGuard использует два int advisory key1179603533/1, shared/exclusive, до8 active
guards/process; nonblocking busy → typed503. Connection detached от pool; original DBAPI handle
явно close на invalidation. PID и lock проверяются, lease одноразовый. Caller выполняет
SQL/ORM на lease.connection и explicit lease.commit(); Session.commit отдельно запрещён.
Для ORM bind использовать эту connection с join_transaction_mode="rollback_only", flush перед
lease.commit(). После потери connection нельзя retry на новом backend в рамках того же lease.

GC delete требует exclusive guard, mtime>24h и однозначного false от authoritative reference
repository текущего UoW. Ошибка/unknown probe не удаляет blob. Metadata GC сначала commit,
затем unlink; pinned/current keys обязан учитывать repository. collect_temp bounded1..10000
scanned entries, удаляет только старые UUID regular single-link files; unknown entries не трогает.
Discovery финальных orphans/retention scheduler и реальные reference queries — BE-025/047;
здесь deletion primitive, staging GC и contract проверены на disposable DB/test reference table.
Новых API/DB tables/migrations нет. Project/file HTTP integration ещё planned.

Точное уточнение crash/connection/rename semantics: [ADR-0009](adr/0009-storage-publication-fencing.md).
Compromised same-UID/root host не изолируется adapter; sandbox — отдельный gate BE-034.
