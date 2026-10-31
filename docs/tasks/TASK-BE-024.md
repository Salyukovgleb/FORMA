---
id: "BE-024"
title: "Локальный FileStorage adapter + тесты безопасности путей"
epic: "EPIC-04"
priority: "P0"
status: "in_review"
depends_on: ["BE-008", "BE-010", "BE-013"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-FILE-001", "FR-FILE-002", "NFR-CONC-001"]
api: []
database: []
tests: ["BE-024-POS", "BE-024-NEG"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage", "0009-storage-publication-fencing"]
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

40 storage scenarios passed; [evidence](../evidence/BE-024.md). Remote CI/merge ожидаются.

## Risks

Symlink race, ENOSPC, failed DB commit. Изменение Outcome требует пересмотра зависимых карточек.

## Mini-plan / dependency review — 2026-10-31

BE-008/010/013 done; BE-024 переведена planned → ready → in_progress после проверки DAG.
BE-019 ждёт BE-024 даже после завершения BE-017/018; поэтому storage adapter — следующий
инкремент критического пути. BE-039 остаётся независимой ready fixture-задачей.
Изучены storage protocol, ADR-0002, threat model и backup/maintenance barrier.

Source: modules/project_files/storage.py (typed ports/value types),
infrastructure/storage/local.py (local adapter), infrastructure/storage/maintenance.py
(PostgreSQL advisory-lock lifecycle); tests/integration/test_file_storage.py и security tests.
Новых публичных routes в этой задаче нет. Конкретные DB объекты при необходимости оформлять
отдельной Alembic revision, не выдавать target schema.sql за runtime metadata.

Tests first: UUID-only physical keys; immutable publish/open; atomic same-filesystem publication
с fsync file/dir без overwrite; traversal, symlink/hardlink и directory replacement race;
ENOSPC/short write/failed fsync, crash до commit; failed DB commit оставляет только orphan.
Maintenance shared/exclusive lock проверять реальными concurrent PostgreSQL connections;
Обнаруженный loss of lock connection запрещает дальнейший publish/commit;
узкое rename window и uncertain COMMIT outcome уточняются ADR-0009.
GC принимает проверенные reference/age данные под exclusive barrier, не удаляет referenced
и свежие blobs; действующие пользовательские volumes не используются в tests.
Тестовые roots только tmp_path/disposable Compose volume. После реализации синхронизировать
storage/runbook/evidence и пройти tests → commit → push → PR → green CI → merge.
Adapter/barrier реализованы; metadata/API integration остаётся BE-019/025.
Локальные и remote результаты фиксируются в evidence после проверки.
