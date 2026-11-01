# Правила инженерной работы FORMA

Владелец: backend-developer. Статус: draft. Обновлено: 2026-10-30. Связи: BE-007, BE-013.

Прочитать docs/README.md, ARCHITECTURAL_REVIEW.md, tasks/STATUS.md и карточку задачи.
Фаза A — только документация, DTO/DDL как проектные артефакты и их validation tooling.
Не начинать продуктовый функционал до завершённой проверки спецификации M0.

Стек: Python/FastAPI/Pydantic2/PostgreSQL/SQLAlchemy2/Alembic, local persistent volume,
PostgreSQL queue, отдельные isolated document attempts. Модули/границы — docs/03_MODULE_BOUNDARIES.md.
Без Redis/Celery/cloud storage/дополнительных служб без ADR и обоснования.

1. Выбирать первую ready задачу без незавершённых depends_on. Planned не ready.
2. Читать requirements, ADR, API, ER, threat model, связанные тесты; записать mini-plan.
3. Feature branch feat/BE-xxx-topic или fix/BE-xxx-topic; безопасно актуализировать от main.
4. Сначала meaningful тесты на основной/негативный сценарий, права и concurrency.
5. Реализовать только Outcome, типизированно, UoW управляет commit; routers без SQL.
6. Синхронно обновлять DTO/OpenAPI/API docs/DDL/dictionary/tasks и ADR при изменении решения.
7. Проверить lint/types/relevant tests/migrations/build; красный тест запрещает готовый commit/DONE.
8. git diff --check, секреты, staged review; атомарный Conventional Commit; push в согласованный remote.
9. Создать PR, дождаться реального green CI для точного head SHA; failed checks исправлять.
10. Merge только согласно protection/review, без force push и обхода checks.
11. Только после merge записать SHA/PR/CI/evidence и done; ожидание review — in_review.

Существующие команды фазы A: make contracts, make lint, make typecheck, make test,
make openapi-check, make schema-check, make ci-local. Продуктовые команды пока planned;
не выдавать их за работающие. При невозможности push/CI указать remote_blocked и точную команду.

Никаких plaintext credentials, логирования токенов/исходников, удаления пользовательских томов,
фиктивных passed/skipped security tests. Обычный worker с БД не security sandbox.
Не менять утверждённые архитектурные решения без ADR. Не создавать пустые файлы ради дерева.

## Переход к фазе B — 2026-10-30

Пользователь принял документацию. PR #1 merged, commit `149419f`; M0 закрыт.
BE-001…007 done. BE-008 выполняется первой; затем BE-010 по зависимостям.
Предыдущие формулировки об ожидании M0 описывают состояние до принятия.

## Текущее состояние — 2026-11-01

M1 foundation (BE-008…013) merged и проверен; BE-014…018 также merged; BE-024 также merged; BE-019 и BE-020 также merged; первая фактически ready BE-039 начата с mini-plan.
Доступны make migrate, migration-check, test-integration, test-migrations, test-security,
dependency-check, dev-up/dev-down и test-compose. CI имеет восемь обязательных checks;
каждый новый PR требует фактического green head SHA перед merge. Runtime реализует18 health/identity/projects методов; остальные28 planned. Head Alembic0003,6 runtime tables. Worker — BE-032.

BE-017 policy интегрирована в project metadata adapters BE-020; auth regression/cleanup CLI BE-018 verified.
BE-024 storage/barrier adapter implemented, ADR-0009 уточняет fencing/uncertain commit.
BE-019 CreateProject/guarded quota/project ORM и BE-020 ACL/revision/7-day metadata CRUD реализованы.
BE-039 — fixtures/matrix mini-plan; converter/sandbox не реализованы. BE-023/025 остаются planned.
