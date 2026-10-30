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

Write protocol: удержать shared global maintenance advisory lock на отдельной connection;
stage → fsync file → rename same filesystem → fsync dir; затем lock owner/project, quota check,
INSERT revision, commit. Потеря DB connection прекращает publisher, не завершать rename после
потери lock. Orphan immutable blobs возможны; DB никогда не ссылается на неопубликованные bytes.
GC берёт exclusive тот же advisory lock, поэтому не пересекается с publisher/backup;
удаляет DB references с учётом snapshots, commit, затем unreferenced blobs older 24h.
GC никогда не удаляет referenced blob. Crash после DB GC до unlink оставляет лишь orphan.

Owner quota 2 GiB всех retained revisions + artifacts; project 500 MiB retained bytes,
2000 live nodes, upload 20 MiB, source text 1 MiB. Проверка quota под lock owner затем project,
без cached counter, SUM по indexed joins для MVP. Диск <10% свободного или <2 GiB → 503
STORAGE_UNAVAILABLE до публикации. Snapshot staging максимум 500 MiB; только один running job
на проект. По умолчанию worker slots=1; общий writable scratch bounded 512 MiB на job.
