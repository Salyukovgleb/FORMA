---
id: "BE-026"
title: "Upload/download, content hashes, storage quotas, cleanup"
epic: "EPIC-04"
priority: "P0"
status: "planned"
depends_on: ["BE-025"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-FILE-001", "FR-FILE-002", "NFR-CONC-001"]
api: ["POST /api/v1/projects/{project_id}/uploads", "GET /api/v1/projects/{project_id}/files/{file_id}/download"]
database: ["file_revisions", "project_nodes", "projects"]
tests: ["BE-026-POS", "BE-026-NEG", "UNIT-API-024", "API-024", "INT-API-024", "SEC-API-024", "UNIT-API-030", "API-030", "INT-API-030", "SEC-API-030"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-026 — Upload/download, content hashes, storage quotas, cleanup

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Upload/download, content hashes, storage quotas, cleanup. Требования: FR-FILE-001, FR-FILE-002, NFR-CONC-001. Цель — следующий проверяемый инкремент milestone M3.

## Outcome

Upload streaming byte limits/MIME/quota; authenticated download сохраняет bytes/hash.

## Preconditions

Зависимости: BE-025. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/modules/project_files/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: POST /api/v1/projects/{project_id}/uploads, GET /api/v1/projects/{project_id}/files/{file_id}/download
Таблицы API: file_revisions, project_nodes, projects
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Upload streaming byte limits/MIME/quota; authenticated download сохраняет bytes/hash.
- Зафиксировать negative test: MIME spoof, upload >20MiB.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-026-POS`: Upload streaming byte limits/MIME/quota; authenticated download сохраняет bytes/hash.
Endpoint tests: UNIT-API-024, API-024, INT-API-024, SEC-API-024, UNIT-API-030, API-030, INT-API-030, SEC-API-030
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-026-NEG`: MIME spoof, upload >20MiB.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Upload streaming byte limits/MIME/quota; authenticated download сохраняет bytes/hash. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

MIME spoof, upload >20MiB. Изменение Outcome требует пересмотра зависимых карточек.
