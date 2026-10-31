---
id: "BE-009"
title: "Docker Compose: API, PostgreSQL, worker; persistent volumes; healthchecks"
epic: "EPIC-01"
priority: "P0"
status: "in_review"
depends_on: ["BE-008", "BE-010"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["NFR-OPS-001"]
api: []
database: []
tests: ["BE-009-POS", "BE-009-NEG"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-009 — Docker Compose: API, PostgreSQL, worker; persistent volumes; healthchecks

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Docker Compose: API, PostgreSQL, worker; persistent volumes; healthchecks. Требования: NFR-OPS-001. Цель — следующий проверяемый инкремент milestone M0.

## Outcome

PostgreSQL стартует; non-root Python image собирается; recreate сохраняет persistent files и DB. API/worker integration — BE-012/032 согласно ADR-0008.

## Preconditions

Зависимости: BE-008, BE-010. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/core/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: Публичный endpoint не добавляется этой задачей.
Таблицы API: Схема/инфраструктурный impact определяется Outcome; целевой DDL в database/schema.sql.
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: PostgreSQL стартует; non-root Python image собирается; recreate сохраняет persistent files и DB. API/worker integration — BE-012/032 согласно ADR-0008.
- Зафиксировать negative test: Recreate контейнера не удаляет volume.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-009-POS`: PostgreSQL стартует; non-root Python image собирается; recreate сохраняет persistent files и DB. API/worker integration — BE-012/032 согласно ADR-0008.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-009-NEG`: Recreate контейнера не удаляет volume.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

PostgreSQL стартует; non-root Python image собирается; recreate сохраняет persistent files и DB. API/worker integration — BE-012/032 согласно ADR-0008. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Recreate контейнера не удаляет volume. Изменение Outcome требует пересмотра зависимых карточек.

## Mini-plan и evidence — 2026-10-31

Docker Engine29.0.1/Compose2.40.3 доступны; внешний блокер снят. ADR-0008 определяет scope.
Сначала scripts/check_compose.py завершился ошибкой на отсутствующем Compose-файле.
Затем добавлены Dockerfile (multi-stage, UID10001), digest-pinned Python/PostgreSQL,
Compose bootstrap с pgdata/files volumes и PostgreSQL healthcheck. API/worker будут BE-012/032.
Runtime/build locks отделены от dev lock. CI docker-build исполняет настоящий smoke.

Локально: make ci-local — 26 passed, lint/types/lock/schema green.
make test-compose — PASS: image import от UID10001; PostgreSQL healthy;
после force-recreate container ID изменился, DB row сохранилась; повторный одноразовый
backend container прочитал сохранённый file; пустой POSTGRES_PASSWORD отклонён.
Тестовый проект уникален; cleanup затрагивает только его labelled volumes; down -v не применяется.

Задача in_review до green CI точного head SHA и merge.
