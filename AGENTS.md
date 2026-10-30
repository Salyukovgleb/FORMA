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
