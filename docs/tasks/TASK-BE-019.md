---
id: "BE-019"
title: "Таблица projects, репозиторий, создание проекта"
epic: "EPIC-03"
priority: "P0"
status: "in_review"
depends_on: ["BE-017", "BE-018", "BE-024"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-PRJ-001", "FR-PRJ-002", "FR-ACL-001"]
api: ["POST /api/v1/projects"]
database: ["users", "auth_sessions", "projects", "project_members"]
tests: ["BE-019-POS", "BE-019-NEG", "UNIT-API-014", "API-014", "INT-API-014", "SEC-API-014"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage", "0009-storage-publication-fencing"]
---

# BE-019 — Таблица projects, репозиторий, создание проекта

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Таблица projects, репозиторий, создание проекта. Требования: FR-PRJ-001, FR-PRJ-002, FR-ACL-001. Цель — следующий проверяемый инкремент milestone M2.

## Outcome

CreateProject атомарно создаёт owner project и учитывает квоту.

## Preconditions

Зависимости: BE-017, BE-018, BE-024. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/modules/projects/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: POST /api/v1/projects
Таблицы: users/auth_sessions (auth), projects/project_members (migration); nodes planned BE-025.
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: CreateProject атомарно создаёт owner project и учитывает квоту.
- Зафиксировать negative test: Превышение user project quota.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-019-POS`: CreateProject атомарно создаёт owner project и учитывает квоту.
Endpoint tests: UNIT-API-014, API-014, INT-API-014, SEC-API-014
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-019-NEG`: Превышение user project quota.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

CreateProject атомарно создаёт owner project и учитывает квоту. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
поведение совпадает с DTO/DDL/ACL; нет незакрытого critical security дефекта.

## Documentation updates

Обновить соответствующий нумерованный документ, endpoint registry при API impact,
DB dictionary при schema impact, [STATUS](STATUS.md) и CHANGELOG для значимого изменения.

## Git/CI checklist

Feature branch → meaningful tests → scoped implementation → lint/types/relevant suites →
diff/secret review → Conventional Commit → push → PR → green SHA checks → required review/merge.
До merge статус не done. Никаких force push, skip checks или удаления volumes.

## Evidence/results

Локальные checks passed; [evidence](../evidence/BE-019.md). Remote CI/merge ожидаются.

## Risks

Превышение user project quota. Изменение Outcome требует пересмотра зависимых карточек.

## Mini-plan / dependency review — 2026-10-31

BE-017/018/024 done, BE-019 planned → ready → in_progress. Выполнен разбор API/DDL,
migration plan, role policy и ADR-0009. CreateProject реализован; evidence после локальных/remote checks.

Source: modules/projects/application.py, schemas.py, router.py; infrastructure/projects/
persistence.py; typed ORM project/member models и Alembic0003_projects_access. SQLAlchemy
metadata UoW bind к MaintenanceGuard.connection, join_transaction_mode="rollback_only",
flush → explicit lease.commit(). Router без SQL, Principal из существующего auth dependency.
Storage adapter не делает metadata commits. Durable audit остаётся BE-046, не fake event.

Согласно утверждённому migration plan0003 создаёт projects/members без main FK;
project_nodes/file_revisions и composite main FK/triggers —0004/BE-025. Не создавать ранние
пустые nodes таблицы ради DTO. До0004 main_file_id должен оставатьсяNULL (проверить временную
DB constraint при migration review); main/engine принадлежат Settings DTO BE-022, Project DTO не расширяется. FK/DDL/model drift и
миграции с seeded identity data должны проверяться отдельно от target schema14tables.

Tests first: unauthenticated401, extra owner_id/role422, whitespace/NUL/invalid Unicode title,
owner из Principal, revision1/engine xelatex/active/default timestamps, пустой project tree,
квота100 retained projects/user с user lock, две concurrent creations у предела99,
revoked/disabled session после ожидания user lock, failed commit без частичного project.
Проверить membership context binding к requester/project; owner не membership row.

template_id=None создаёт пустой project. Не игнорировать non-null template_id: explicit
unsupported/unknown template response документируется до BE-021 (templates требуют BE-025/027).
Новые routes — только POST /api/v1/projects в этой задаче; listing/read/update —BE-020.
Обновить runtime/canonical DTO, registry/OpenAPI, migration dictionary/runbook и Docker heads/smoke;
проверить fresh/seeded/idempotent upgrade, FK/checks, downgrade только disposable test DB.
Затем lint/types/relevant/security/migrations/compose → commit → push → PR → green SHA CI → merge.

## Implementation verification — 2026-11-01

POST CreateProject и0003 projects/members реализованы. Квота429 QUOTA_EXCEEDED на retained
active+deleted, Retry-After86400 без обещания reset. Defaults и runtime DTO проверены;
main/engine — DB/Settings, не новые поля Project response. template_id non-null404 доBE-021.
Shared JSON2MiB/MIME и Unicode validation переиспользуются из core. Guarded ORM rollback_only
flush/commit проверены реальными constraints и different-session quota race. User/session
revalidation после ожидания lock; operational SQL failures →503, lock2s/statement5s.
Все локальные результаты в evidence; durable audit/project read/update ещё planned.
