---
id: "BE-043"
title: "ZIP export исходников, исключения, защита от zip slip"
epic: "EPIC-06"
priority: "P0"
status: "planned"
depends_on: ["BE-033", "BE-034"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-DOC-002", "FR-DOC-003"]
api: []
database: []
tests: ["BE-043-POS", "BE-043-NEG"]
adr: ["0001-modular-monolith", "0004-isolated-document-processing"]
---

# BE-043 — ZIP export исходников, исключения, защита от zip slip

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

ZIP export исходников, исключения, защита от zip slip. Требования: FR-DOC-002, FR-DOC-003. Цель — следующий проверяемый инкремент milestone M5.

## Outcome

ZIP содержит ровно manifest paths и пустые папки, без служебных файлов.

## Preconditions

Зависимости: BE-033, BE-034. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/infrastructure/conversion/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: Публичный endpoint не добавляется этой задачей.
Таблицы API: Схема/инфраструктурный impact определяется Outcome; целевой DDL в database/schema.sql.
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: ZIP содержит ровно manifest paths и пустые папки, без служебных файлов.
- Зафиксировать negative test: Traversal/absolute member path.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-043-POS`: ZIP содержит ровно manifest paths и пустые папки, без служебных файлов.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-043-NEG`: Traversal/absolute member path.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

ZIP содержит ровно manifest paths и пустые папки, без служебных файлов. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Traversal/absolute member path. Изменение Outcome требует пересмотра зависимых карточек.
