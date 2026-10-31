# Roadmap

Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30. Связи: BE-001…052.

| Milestone | Выход | Диапазон |
|---|---|---|
| M0 | Проверенная спецификация | BE-001–007 |
| M1 | Foundation + CI | BE-008–013 |
| M2 | Auth + projects + roles | BE-014–023 (template/settings также зависят от files) |
| M3 | Files/revisions/concurrency | BE-024–030 |
| M4 | Isolated PDF | BE-031–038 |
| M5 | DOCX/ZIP | BE-039–045 |
| M6 | Recovery/security/release | BE-046–052 |

Порядок допускает ранний BE-024 для CreateProject и BE-025 для templates/settings;
номера задач не заменяют [DAG](DEPENDENCIES.md). Frontend integration demos:
BE-015 первая регистрация/login; BE-019 первый проект; BE-027 save/409;
BE-037 PDF; BE-044 DOCX/ZIP. Mock frontend может работать с OpenAPI уже после M0.

Сейчас **0 ready задач реализации**: документация in_review, M0 не merged/approved.
Первые пять кандидатов после закрытия M0: BE-008 → BE-010 → BE-009 → BE-011 → BE-012.
BE-013 затем включает product CI, до product features. Нельзя одновременно объявить эти
пять ready: у них последовательные dependencies. BE-039 доступна как отдельная fixture-ветка после M0.

Предварительная оценка для одного разработчика: 45–100 developer days базовой реализации,
плюс 15–30 дней резерва на sandbox, DOCX fidelity и recovery. Это диапазон планирования,
не обещание даты; уточнить после M1 и первого DOCX fixture. Оценки задач не включают ожидание review.

## Переход к фазе B — 2026-10-30

Пользователь принял документацию. PR #1 merged, commit `149419f`; M0 закрыт.
BE-001…007 done. BE-008 выполняется первой; затем BE-010 по зависимостям.
Предыдущие формулировки об ожидании M0 описывают состояние до принятия.

## M1 foundation closed — 2026-10-31

BE-008…013 done: package/config, persistent PostgreSQL/image, typed DB/Alembic,
реальный health API и восемь CI checks. Worker runtime остаётся BE-032 согласно ADR-0008,
проверки всей системы — BE-051. Следующая ready задача по критическому пути — BE-014.
Миграции проверены в disposable DB; это не заявление о применении к пользовательской БД.

## Identity increment — 2026-10-31

BE-014…018 done после green CI/merge: registration, sessions/JWT, profile/password,
чистая role/object policy и auth limit regression/cleanup. M2 ещё не закрыт: BE-019…023 pending.
BE-019 зависит от FileStorage BE-024, все prerequisites BE-024 done; следующий инкремент — BE-024.
BE-039 остаётся независимой ready задачей. Не начинать CreateProject с незакрытым storage dependency.
