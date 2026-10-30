---
id: "BE-021"
title: "Встроенные шаблоны и создание проекта из шаблона"
epic: "EPIC-03"
priority: "P0"
status: "planned"
depends_on: ["BE-019", "BE-025", "BE-027"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-PRJ-001", "FR-PRJ-002", "FR-ACL-001"]
api: ["GET /api/v1/templates", "GET /api/v1/templates/{template_id}"]
database: ["project_members", "project_nodes", "projects"]
tests: ["BE-021-POS", "BE-021-NEG", "UNIT-API-045", "API-045", "INT-API-045", "SEC-API-045", "UNIT-API-046", "API-046", "INT-API-046", "SEC-API-046"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-021 — Встроенные шаблоны и создание проекта из шаблона

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Встроенные шаблоны и создание проекта из шаблона. Требования: FR-PRJ-001, FR-PRJ-002, FR-ACL-001. Цель — следующий проверяемый инкремент milestone M2.

## Outcome

Versioned sample template создаёт полноценный проект с main.tex и зависимостями.

## Preconditions

Зависимости: BE-019, BE-025, BE-027. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/modules/projects/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: GET /api/v1/templates, GET /api/v1/templates/{template_id}
Таблицы API: project_members, project_nodes, projects
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Versioned sample template создаёт полноценный проект с main.tex и зависимостями.
- Зафиксировать negative test: Неизвестный template_id.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-021-POS`: Versioned sample template создаёт полноценный проект с main.tex и зависимостями.
Endpoint tests: UNIT-API-045, API-045, INT-API-045, SEC-API-045, UNIT-API-046, API-046, INT-API-046, SEC-API-046
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-021-NEG`: Неизвестный template_id.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Versioned sample template создаёт полноценный проект с main.tex и зависимостями. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Неизвестный template_id. Изменение Outcome требует пересмотра зависимых карточек.
