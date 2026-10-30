---
id: "BE-045"
title: "Golden-file / structural regression tests PDF и Word на fixtures"
epic: "EPIC-06"
priority: "P0"
status: "planned"
depends_on: ["BE-038", "BE-044"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-DOC-002", "FR-DOC-003"]
api: []
database: []
tests: ["BE-045-POS", "BE-045-NEG"]
adr: ["0001-modular-monolith", "0004-isolated-document-processing"]
---

# BE-045 — Golden-file / structural regression tests PDF и Word на fixtures

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Golden-file / structural regression tests PDF и Word на fixtures. Требования: FR-DOC-002, FR-DOC-003. Цель — следующий проверяемый инкремент milestone M5.

## Outcome

Structural regression PDF/DOCX стабилен при timestamp/relationship ID noise.

## Preconditions

Зависимости: BE-038, BE-044. Для реализации они должны быть done;
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

- Написать positive test: Structural regression PDF/DOCX стабилен при timestamp/relationship ID noise.
- Зафиксировать negative test: Потеря caption/math ловится regression.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-045-POS`: Structural regression PDF/DOCX стабилен при timestamp/relationship ID noise.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-045-NEG`: Потеря caption/math ловится regression.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Structural regression PDF/DOCX стабилен при timestamp/relationship ID noise. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Потеря caption/math ловится regression. Изменение Outcome требует пересмотра зависимых карточек.
