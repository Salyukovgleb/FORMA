---
id: "BE-030"
title: "Интеграционные тесты файлов на конкурентность и отказоустойчивость"
epic: "EPIC-04"
priority: "P0"
status: "planned"
depends_on: ["BE-026", "BE-028", "BE-029"]
owner: "backend-developer"
estimate: "2–4 developer days"
requirements: ["FR-FILE-001", "FR-FILE-002", "NFR-CONC-001"]
api: []
database: []
tests: ["BE-030-POS", "BE-030-NEG"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-030 — Интеграционные тесты файлов на конкурентность и отказоустойчивость

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Интеграционные тесты файлов на конкурентность и отказоустойчивость. Требования: FR-FILE-001, FR-FILE-002, NFR-CONC-001. Цель — следующий проверяемый инкремент milestone M3.

## Outcome

Crash matrix и конкурентные tree/save/quota операции сохраняют DB/blob согласованность.

## Preconditions

Зависимости: BE-026, BE-028, BE-029. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/modules/project_files/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: Публичный endpoint не добавляется этой задачей.
Таблицы API: Схема/инфраструктурный impact определяется Outcome; целевой DDL в database/schema.sql.
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Crash matrix и конкурентные tree/save/quota операции сохраняют DB/blob согласованность.
- Зафиксировать negative test: Crash после rename до DB commit.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-030-POS`: Crash matrix и конкурентные tree/save/quota операции сохраняют DB/blob согласованность.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-030-NEG`: Crash после rename до DB commit.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Crash matrix и конкурентные tree/save/quota операции сохраняют DB/blob согласованность. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Crash после rename до DB commit. Изменение Outcome требует пересмотра зависимых карточек.
