# Доменные сущности

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

| Сущность | Инварианты | Жизненный цикл / право |
|---|---|---|
| Project | Один неизменяемый owner_id; main принадлежит проекту | active → deleted → active до 7 суток; owner purge |
| ProjectMember | Только editor/viewer; owner вычисляется отдельно | grant/change/remove только owner; self-leave кроме owner |
| ProjectNode | NFC имя; parent folder same project; live path unique | create → rename/move → soft delete; writer |
| Revision | bytes/hash/author неизменяемы | append; restore создаёт новую; GC после retention |
| Snapshot | Пути и ссылки revision фиксированы | создание с job; GC после удаления job |
| DocumentJob | Терминальное состояние неизменно; fencing | queue/retry/running/terminal; worker |
| Artifact | Опубликован только для succeeded; hash verified | read до expiry, затем GC |
| AuthSession | Absolute expiry; hashes only | rotate/revoke/expire; own user |

`project_nodes.revision` — версия метаданных узла; content revision — последний
`file_revisions.revision` по node_id. В DTO Node явно два поля revision/content_revision.
Save увеличивает оба счётчика и project revision; rename увеличивает metadata/project,
но не content revision. Restore увеличивает content revision, никогда не перематывает её.
Project revision увеличивается при настройках, структуре, содержимом, metadata/delete/restore;
изменение ACL не меняет snapshot input, но сериализуется тем же project lock.
