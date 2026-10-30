# Требования и трассировка

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

| ID | Норма | Задачи | Приёмка |
|---|---|---|---|
| FR-AUTH-001 | Регистрация/login, rotating refresh, отзыв сессий, профиль/пароль | BE-014–018 | Replay отзывает семейство session; logout немедленный |
| FR-PRJ-001 | CRUD, templates, settings | BE-019–022 | Main только live .tex того же проекта |
| FR-PRJ-002 | Удаление/restore/retention | BE-020,047 | Restore до 7 суток, проверенный backup |
| FR-ACL-001 | owner/editor/viewer | BE-017,023 | Матрица прав и cross-project IDOR |
| FR-FILE-001 | UTF-8, uploads, revisions, optimistic save | BE-024–027,029–030 | 409 не меняет текущий blob |
| FR-FILE-002 | Атомарное дерево | BE-025,028,030 | Нет циклов, коллизий, symlink escape |
| FR-DOC-001 | Snapshot → sandbox PDF | BE-031–038 | Lease fencing, timeout, безопасный output |
| FR-DOC-002 | Исходник → editable DOCX | BE-039–042,045 | OMML/таблицы/стили и warnings |
| FR-DOC-003 | ZIP исходников | BE-043–044 | Только manifest, корректный Unicode |
| NFR-SEC-001 | ACL, input bounds, secrets, изоляция | BE-007,018,034,049 | SEC suites обязательны |
| NFR-CONC-001 | Atomic state, retries, conflicts | BE-027,030–033 | Конкурентные реальные транзакции |
| NFR-OPS-001 | Backup, журнал, воспроизводимость | BE-009–013,046–052 | Clean install + restore rehearsal |

Детальная трассировка каждого метода к DTO, ACL, таблицам и тестовым ID:
[машинный реестр](contracts/endpoints.json). Обозначения API-001…046 — методы;
API-001/INT-API-001/SEC-API-001/UNIT-API-001 в полях tests — пространства тестовых ID,
статус всех поведенческих тестов planned. Исполняемые проверки фазы A проверяют схемы,
DDL и документацию; они не доказывают реализацию требований.
