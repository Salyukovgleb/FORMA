---
id: "BE-025"
title: "Модель дерева, папки/файлы, ограничение допустимых расширений"
epic: "EPIC-04"
priority: "P0"
status: "planned"
depends_on: ["BE-019", "BE-024"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-FILE-001", "FR-FILE-002", "NFR-CONC-001"]
api: ["GET /api/v1/projects/{project_id}/tree", "POST /api/v1/projects/{project_id}/folders", "POST /api/v1/projects/{project_id}/files", "GET /api/v1/projects/{project_id}/nodes/{node_id}"]
database: ["file_revisions", "project_nodes", "projects"]
tests: ["BE-025-POS", "BE-025-NEG", "UNIT-API-021", "API-021", "INT-API-021", "SEC-API-021", "UNIT-API-022", "API-022", "INT-API-022", "SEC-API-022", "UNIT-API-023", "API-023", "INT-API-023", "SEC-API-023", "UNIT-API-025", "API-025", "INT-API-025", "SEC-API-025"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-025 — Модель дерева, папки/файлы, ограничение допустимых расширений

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Модель дерева, папки/файлы, ограничение допустимых расширений. Требования: FR-FILE-001, FR-FILE-002, NFR-CONC-001. Цель — следующий проверяемый инкремент milestone M3.

## Outcome

Создаются folders/files, NFC paths и metadata/content revisions согласованы.

## Preconditions

Зависимости: BE-019, BE-024. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/modules/project_files/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: GET /api/v1/projects/{project_id}/tree, POST /api/v1/projects/{project_id}/folders, POST /api/v1/projects/{project_id}/files, GET /api/v1/projects/{project_id}/nodes/{node_id}
Таблицы API: file_revisions, project_nodes, projects
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Создаются folders/files, NFC paths и metadata/content revisions согласованы.
- Зафиксировать negative test: Case/NFC collision, invalid parent.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-025-POS`: Создаются folders/files, NFC paths и metadata/content revisions согласованы.
Endpoint tests: UNIT-API-021, API-021, INT-API-021, SEC-API-021, UNIT-API-022, API-022, INT-API-022, SEC-API-022, UNIT-API-023, API-023, INT-API-023, SEC-API-023, UNIT-API-025, API-025, INT-API-025, SEC-API-025
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-025-NEG`: Case/NFC collision, invalid parent.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Создаются folders/files, NFC paths и metadata/content revisions согласованы. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Case/NFC collision, invalid parent. Изменение Outcome требует пересмотра зависимых карточек.
