---
id: "BE-049"
title: "Security review: IDOR, path traversal, ZIP, sandbox, auth"
epic: "EPIC-07"
priority: "P0"
status: "planned"
depends_on: ["BE-018", "BE-030", "BE-038", "BE-042", "BE-043", "BE-046"]
owner: "backend-developer"
estimate: "2–4 developer days"
requirements: ["NFR-OPS-001", "NFR-SEC-001"]
api: []
database: []
tests: ["BE-049-POS", "BE-049-NEG"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-049 — Security review: IDOR, path traversal, ZIP, sandbox, auth

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Security review: IDOR, path traversal, ZIP, sandbox, auth. Требования: NFR-OPS-001, NFR-SEC-001. Цель — следующий проверяемый инкремент milestone M6.

## Outcome

IDOR/path/auth/sandbox/ZIP review не содержит незакрытых critical findings.

## Preconditions

Зависимости: BE-018, BE-030, BE-038, BE-042, BE-043, BE-046. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/infrastructure/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: Публичный endpoint не добавляется этой задачей.
Таблицы API: Схема/инфраструктурный impact определяется Outcome; целевой DDL в database/schema.sql.
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: IDOR/path/auth/sandbox/ZIP review не содержит незакрытых critical findings.
- Зафиксировать negative test: Не учитывать skipped sandbox как pass.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-049-POS`: IDOR/path/auth/sandbox/ZIP review не содержит незакрытых critical findings.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-049-NEG`: Не учитывать skipped sandbox как pass.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

IDOR/path/auth/sandbox/ZIP review не содержит незакрытых critical findings. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Не учитывать skipped sandbox как pass. Изменение Outcome требует пересмотра зависимых карточек.
