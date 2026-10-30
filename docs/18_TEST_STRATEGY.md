# Стратегия проверок

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

Тесты фазы A: Pydantic examples/validation, OpenAPI validation, 46 routes uniqueness,
DB dictionary coverage, SQL на disposable PostgreSQL, DAG 52 задач и ссылки.
Это не продуктовые API/security тесты. Поведенческие ID находятся в endpoint registry и cards.

| Suite | Fixture / сценарий | Задачи |
|---|---|---|
| unit | ACL matrix, state transitions, path/name normalization | BE-017,024,031 |
| integration | Real PostgreSQL; rollback между blob publish и DB commit | BE-011,030 |
| api | Все 46 routes: positive/error/auth/input schema | BE-014–044,050 |
| security | Два пользователя/проекта; IDOR, refresh replay, traversal | BE-018,049 |
| workers | Два claims, stale heartbeat, cancellation race, retries | BE-032,038 |
| fidelity | ru text, math, tables, images, footnotes, bib, long fixture | BE-039–045 |
| recovery | Consistent backup DB+files; restore compare SHA256/counts | BE-047,051 |
| performance | 20 users, 2000-node project, 2 competing workers | BE-048 |

Критические concurrency тесты используют barriers, а не sleep guesses. Отдельная test DB,
fixture IDs, отдельный tmp_path, запрет подключения к production URL. Migration suite проверяет
seeded предыдущую версию. PDF checks meaningful text/pages, DOCX OOXML structure; versioned
fixtures хранят исходник и expected structural assertions, а не огромные binary diffs.
Новые defects получают regression test. Coverage дополнительный сигнал, не замена проверок.
CI skips нельзя считать success evidence для sandbox; missing daemon означает failed gate
для задач, где sandbox требуется. Фаза A не запускает отсутствующие product suites.
