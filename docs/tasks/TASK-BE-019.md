---
id: "BE-019"
title: "Таблица projects, репозиторий, создание проекта"
epic: "EPIC-03"
priority: "P0"
status: "planned"
depends_on: ["BE-017", "BE-018", "BE-024"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-PRJ-001", "FR-PRJ-002", "FR-ACL-001"]
api: ["POST /api/v1/projects"]
database: ["project_members", "project_nodes", "projects"]
tests: ["BE-019-POS", "BE-019-NEG", "UNIT-API-014", "API-014", "INT-API-014", "SEC-API-014"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
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
Таблицы API: project_members, project_nodes, projects
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

planned; code/tests/commit/PR/CI отсутствуют, поведение не проверено.

## Risks

Превышение user project quota. Изменение Outcome требует пересмотра зависимых карточек.
