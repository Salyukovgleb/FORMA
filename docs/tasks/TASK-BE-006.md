---
id: "BE-006"
title: "Архитектура хранения, обработки фоновых заданий, PDF и DOCX"
epic: "EPIC-00"
priority: "P0"
status: "done"
depends_on: ["BE-003", "BE-004", "BE-005"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["NFR-OPS-001"]
api: []
database: []
tests: ["BE-006-POS", "BE-006-NEG"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-006 — Архитектура хранения, обработки фоновых заданий, PDF и DOCX

Владелец: backend-developer. Документ: approved. Обновлено: 2026-10-30.

## Context

Архитектура хранения, обработки фоновых заданий, PDF и DOCX. Требования: NFR-OPS-001. Цель — следующий проверяемый инкремент milestone M0.

## Outcome

Определены atomic publish, GC, snapshot, lease fencing и sandbox launcher.

## Preconditions

Зависимости: BE-003, BE-004, BE-005. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`docs/`; соответствующие tests/contracts/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: Публичный endpoint не добавляется этой задачей.
Таблицы API: Схема/инфраструктурный impact определяется Outcome; целевой DDL в database/schema.sql.
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Определены atomic publish, GC, snapshot, lease fencing и sandbox launcher.
- Зафиксировать negative test: GC не удаляет publishing/pinned blobs.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-006-POS`: Определены atomic publish, GC, snapshot, lease fencing и sandbox launcher.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-006-NEG`: GC не удаляет publishing/pinned blobs.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Определены atomic publish, GC, snapshot, lease fencing и sandbox launcher. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
поведение совпадает с DTO/DDL/ACL; нет незакрытого critical security дефекта.

## Documentation updates

Обновить соответствующий нумерованный документ, endpoint registry при API impact,
DB dictionary при schema impact, [STATUS](STATUS.md) и CHANGELOG для значимого изменения.

## Git/CI checklist

Feature branch → meaningful tests → scoped implementation → lint/types/relevant suites →
diff/secret review → Conventional Commit → push → PR → green SHA checks → required review/merge.
До merge статус не done. Никаких force push, skip checks или удаления volumes.

## Evidence/results

Проектный артефакт подготовлен в фазе A; статус in_review. Проверки см. ../evidence/phase-a.md. Merge отсутствует.

## Risks

GC не удаляет publishing/pinned blobs. Изменение Outcome требует пересмотра зависимых карточек.

Принято пользователем 2026-10-30; PR #1 merged в main: `149419f6644bf9da3a27e16c078d4239b6ad4220`. CI head `8dd7717` success. M0 закрыт.
