---
id: "BE-009"
title: "Docker Compose: API, PostgreSQL, worker; persistent volumes; healthchecks"
epic: "EPIC-01"
priority: "P0"
status: "blocked"
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

API/Postgres/worker стартуют; recreate сохраняет persistent files и DB.

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

- Написать positive test: API/Postgres/worker стартуют; recreate сохраняет persistent files и DB.
- Зафиксировать negative test: Recreate контейнера не удаляет volume.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-009-POS`: API/Postgres/worker стартуют; recreate сохраняет persistent files и DB.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-009-NEG`: Recreate контейнера не удаляет volume.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

API/Postgres/worker стартуют; recreate сохраняет persistent files и DB. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

## Readiness / блокер — 2026-10-31

BE-008 и BE-010 merged. Docker CLI установлен, но docker info возвращает exit1:
нет unix socket ~/.docker/run/docker.sock. docker desktop status не завершился за 8s.
Ранее выполненный open -a Docker не восстановил daemon. UI tool сообщил:
Computer Use permissions are not granted. Проверить экран Docker Desktop из сессии нельзя.
Нужно завершить запуск Docker Desktop на компьютере пользователя; затем `docker info`
должен показывать Server, после чего выполнить контейнерные тесты. Данные/volumes не удалялись.

Также обнаружена неполнота исходного DAG: BE-009 требует стартующих API/worker,
но app factory появляется в BE-012 (через BE-011, зависящую от BE-009),
а worker loop — в BE-032. До реализации необходимо разделить инфраструктурный bootstrap
и финальную проверку runtime persistence; не заменять API/worker sleep-процессами.
Этот вопрос требует отдельного ADR и корректировки задач до продуктового кода.
