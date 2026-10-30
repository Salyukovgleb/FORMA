---
id: "BE-028"
title: "Move/rename/delete, atomicity и невозможность циклов дерева"
epic: "EPIC-04"
priority: "P0"
status: "planned"
depends_on: ["BE-027"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-FILE-001", "FR-FILE-002", "NFR-CONC-001"]
api: ["PATCH /api/v1/projects/{project_id}/nodes/{node_id}", "DELETE /api/v1/projects/{project_id}/nodes/{node_id}"]
database: ["file_revisions", "project_nodes", "projects"]
tests: ["BE-028-POS", "BE-028-NEG", "UNIT-API-028", "API-028", "INT-API-028", "SEC-API-028", "UNIT-API-029", "API-029", "INT-API-029", "SEC-API-029"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-028 — Move/rename/delete, atomicity и невозможность циклов дерева

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Move/rename/delete, atomicity и невозможность циклов дерева. Требования: FR-FILE-001, FR-FILE-002, NFR-CONC-001. Цель — следующий проверяемый инкремент milestone M3.

## Outcome

Rename/move/delete поддерева атомарны, cycles/main-in-use запрещены.

## Preconditions

Зависимости: BE-027. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/modules/project_files/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: PATCH /api/v1/projects/{project_id}/nodes/{node_id}, DELETE /api/v1/projects/{project_id}/nodes/{node_id}
Таблицы API: file_revisions, project_nodes, projects
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Rename/move/delete поддерева атомарны, cycles/main-in-use запрещены.
- Зафиксировать negative test: Move в собственного descendant.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-028-POS`: Rename/move/delete поддерева атомарны, cycles/main-in-use запрещены.
Endpoint tests: UNIT-API-028, API-028, INT-API-028, SEC-API-028, UNIT-API-029, API-029, INT-API-029, SEC-API-029
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-028-NEG`: Move в собственного descendant.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Rename/move/delete поддерева атомарны, cycles/main-in-use запрещены. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Move в собственного descendant. Изменение Outcome требует пересмотра зависимых карточек.
