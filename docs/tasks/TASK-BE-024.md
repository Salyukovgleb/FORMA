---
id: "BE-024"
title: "Локальный FileStorage adapter + тесты безопасности путей"
epic: "EPIC-04"
priority: "P0"
status: "planned"
depends_on: ["BE-008", "BE-010", "BE-013"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-FILE-001", "FR-FILE-002", "NFR-CONC-001"]
api: []
database: []
tests: ["BE-024-POS", "BE-024-NEG"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-024 — Локальный FileStorage adapter + тесты безопасности путей

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Локальный FileStorage adapter + тесты безопасности путей. Требования: FR-FILE-001, FR-FILE-002, NFR-CONC-001. Цель — следующий проверяемый инкремент milestone M3.

## Outcome

UUID blob publish/open/GC безопасны к traversal, symlink и crash до commit.

## Preconditions

Зависимости: BE-008, BE-010, BE-013. Для реализации они должны быть done;
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

- Написать positive test: UUID blob publish/open/GC безопасны к traversal, symlink и crash до commit.
- Зафиксировать negative test: Symlink race, ENOSPC, failed DB commit.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-024-POS`: UUID blob publish/open/GC безопасны к traversal, symlink и crash до commit.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-024-NEG`: Symlink race, ENOSPC, failed DB commit.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

UUID blob publish/open/GC безопасны к traversal, symlink и crash до commit. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Symlink race, ENOSPC, failed DB commit. Изменение Outcome требует пересмотра зависимых карточек.
