# FORMA — документация backend

Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30. Связи: BE-001–007.

Фаза A: проектные артефакты подготовлены, продуктовая реализация planned.
[Architectural Review](ARCHITECTURAL_REVIEW.md) · [Аудит](REPOSITORY_AUDIT.md) ·
[Evidence](evidence/phase-a.md) · [Статус задач](tasks/STATUS.md).

## Карта чтения

- Backend: 02 → 03 → 04 → 05/06 → 08/09 → task card.
- Frontend: 00 → 08/09 → api/ → 10 → 15 → 22 → examples/.
- QA/security: 01 → 16 → 18 → 23 → 24 → task NEG scenarios.
- Operations: 11 → 12 → 14 → 17 → 20/21 → runbooks/.

## Спецификация

- [00_PRODUCT_AND_SCOPE](00_PRODUCT_AND_SCOPE.md)
- [01_REQUIREMENTS](01_REQUIREMENTS.md)
- [02_ARCHITECTURE](02_ARCHITECTURE.md)
- [03_MODULE_BOUNDARIES](03_MODULE_BOUNDARIES.md)
- [04_DOMAIN_MODEL](04_DOMAIN_MODEL.md)
- [05_DATA_MODEL](05_DATA_MODEL.md)
- [06_DATABASE_DICTIONARY](06_DATABASE_DICTIONARY.md)
- [07_MIGRATION_PLAN](07_MIGRATION_PLAN.md)
- [08_API_CONVENTIONS](08_API_CONVENTIONS.md)
- [09_API_ENDPOINT_CATALOG](09_API_ENDPOINT_CATALOG.md)
- [10_AUTH_AND_AUTHORIZATION](10_AUTH_AND_AUTHORIZATION.md)
- [11_LOCAL_FILE_STORAGE](11_LOCAL_FILE_STORAGE.md)
- [12_PDF_COMPILATION](12_PDF_COMPILATION.md)
- [13_DOCX_EXPORT](13_DOCX_EXPORT.md)
- [14_JOB_QUEUE_AND_RETRIES](14_JOB_QUEUE_AND_RETRIES.md)
- [15_ERROR_MODEL](15_ERROR_MODEL.md)
- [16_SECURITY_THREAT_MODEL](16_SECURITY_THREAT_MODEL.md)
- [17_OBSERVABILITY](17_OBSERVABILITY.md)
- [18_TEST_STRATEGY](18_TEST_STRATEGY.md)
- [19_CI_CD_AND_GIT](19_CI_CD_AND_GIT.md)
- [20_DOCKER_AND_LOCAL_RUN](20_DOCKER_AND_LOCAL_RUN.md)
- [21_OPERATIONS_BACKUP_RESTORE](21_OPERATIONS_BACKUP_RESTORE.md)
- [22_FRONTEND_BACKEND_CONTRACT](22_FRONTEND_BACKEND_CONTRACT.md)
- [23_NON_FUNCTIONAL_REQUIREMENTS](23_NON_FUNCTIONAL_REQUIREMENTS.md)
- [24_RELEASE_AND_ACCEPTANCE](24_RELEASE_AND_ACCEPTANCE.md)
- [25_POST_MVP](25_POST_MVP.md)

## Контракты и решения


### api

- [access.md](api/access.md)
- [documents.md](api/documents.md)
- [identity.md](api/identity.md)
- [jobs.md](api/jobs.md)
- [project-files.md](api/project-files.md)
- [projects.md](api/projects.md)
- [system.md](api/system.md)

### adr

- [0001-modular-monolith.md](adr/0001-modular-monolith.md)
- [0002-local-filesystem-storage.md](adr/0002-local-filesystem-storage.md)
- [0003-postgres-job-queue.md](adr/0003-postgres-job-queue.md)
- [0004-isolated-document-processing.md](adr/0004-isolated-document-processing.md)
- [0005-docx-export-strategy.md](adr/0005-docx-export-strategy.md)
- [0006-auth-and-dependencies.md](adr/0006-auth-and-dependencies.md)
- [0007-retention-and-snapshots.md](adr/0007-retention-and-snapshots.md)

### diagrams

- [compile-sequence.mmd](diagrams/compile-sequence.mmd)
- [containers.mmd](diagrams/containers.mmd)
- [context.mmd](diagrams/context.mmd)
- [er.mmd](diagrams/er.mmd)
- [export-sequence.mmd](diagrams/export-sequence.mmd)
- [job-lifecycle.mmd](diagrams/job-lifecycle.mmd)
- [modules.mmd](diagrams/modules.mmd)
- [task-dependencies.mmd](diagrams/task-dependencies.mmd)

### decisions

- [assumptions.md](decisions/assumptions.md)
- [open-questions.md](decisions/open-questions.md)

### runbooks

- [backup-restore.md](runbooks/backup-restore.md)
- [ci-failure.md](runbooks/ci-failure.md)
- [compilation-debug.md](runbooks/compilation-debug.md)
- [failed-job.md](runbooks/failed-job.md)
- [local-start.md](runbooks/local-start.md)
- [migrations.md](runbooks/migrations.md)

### examples

- [sample-errors.json](examples/sample-errors.json)
- [sample-job.json](examples/sample-job.json)
- [sample-project.json](examples/sample-project.json)

## Машинные артефакты

[Pydantic DTO](contracts/models.py) · [Registry](contracts/registry.py) ·
[OpenAPI](contracts/openapi.json) · [Endpoint traceability](contracts/endpoints.json) ·
[SQL DDL](database/schema.sql) · [SQL examples](database/examples.sql).

## Задачи

[Roadmap](tasks/ROADMAP.md) · [DAG](tasks/DEPENDENCIES.md) · [Status](tasks/STATUS.md) ·
[Все 52 карточки через registry](tasks/tasks.json) · [Правила карты](tasks/README.md).

## Фактическая структура

```text
README.md, AGENTS.md, CONTRIBUTING.md, CHANGELOG.md, .env.example
Makefile, pyproject.toml, requirements-dev.in, requirements-dev.lock
.github/workflows/ci.yml, .github/pull_request_template.md, .github/ISSUE_TEMPLATE/task.yml
docs/00…25, REPOSITORY_AUDIT.md, ARCHITECTURAL_REVIEW.md, REFERENCES.md
docs/api/ (7), contracts/ (DTO, registry, OpenAPI, traceability)
docs/database/ (DDL, examples, table registry)
docs/adr/ (7), diagrams/ (8), decisions/, runbooks/ (6), examples/, evidence/
docs/tasks/ (52 cards, 8 epics, roadmap, DAG, status, template, registry)
scripts/build_contracts.py, scripts/check_schema.py
tests/contracts/test_specification.py
```

src/, alembic/, runtime Compose и product tests создаются в фазе B; пустые placeholders
не добавлены. [Технические источники](REFERENCES.md). Все документы draft до review;
контрактные tests не означают, что planned endpoints работают.

## Переход к фазе B — 2026-10-30

Пользователь принял документацию. PR #1 merged, commit `149419f`; M0 закрыт.
BE-001…007 done. BE-008 выполняется первой; затем BE-010 по зависимостям.
Предыдущие формулировки об ожидании M0 описывают состояние до принятия.

[ADR-0008: порядок Compose/runtime интеграции](adr/0008-foundation-integration-order.md).
