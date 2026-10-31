---
id: "BE-032"
title: "Worker process, heartbeats, stale jobs, cancellation"
epic: "EPIC-05"
priority: "P0"
status: "planned"
depends_on: ["BE-031"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-DOC-001", "NFR-SEC-001"]
api: []
database: []
tests: ["BE-032-POS", "BE-032-NEG"]
adr: ["0001-modular-monolith", "0004-isolated-document-processing"]
---

# BE-032 — Worker process, heartbeats, stale jobs, cancellation

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Worker process, heartbeats, stale jobs, cancellation. Требования: FR-DOC-001, NFR-SEC-001. Цель — следующий проверяемый инкремент milestone M4.

## Outcome

Heartbeat/reaper/cancel не позволяют stale worker опубликовать результат.

## Preconditions

Зависимости: BE-031. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/infrastructure/workers/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: Публичный endpoint не добавляется этой задачей.
Таблицы API: Схема/инфраструктурный impact определяется Outcome; целевой DDL в database/schema.sql.
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Heartbeat/reaper/cancel не позволяют stale worker опубликовать результат.
- Зафиксировать negative test: Complete после lease expiry/cancel.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-032-POS`: Heartbeat/reaper/cancel не позволяют stale worker опубликовать результат.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-032-NEG`: Complete после lease expiry/cancel.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Heartbeat/reaper/cancel не позволяют stale worker опубликовать результат. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Complete после lease expiry/cancel. Изменение Outcome требует пересмотра зависимых карточек.

ADR-0008 integration gate: Добавить настоящий Compose worker service с heartbeat smoke; не sleep placeholder.
