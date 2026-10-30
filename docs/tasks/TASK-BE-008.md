---
id: "BE-008"
title: "Структура Python-проекта, форматирование, типизация, lint"
epic: "EPIC-01"
priority: "P0"
status: "done"
depends_on: ["BE-007"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["NFR-OPS-001"]
api: []
database: []
tests: ["BE-008-POS", "BE-008-NEG"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-008 — Структура Python-проекта, форматирование, типизация, lint

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Структура Python-проекта, форматирование, типизация, lint. Требования: NFR-OPS-001. Цель — следующий проверяемый инкремент milestone M1.

## Outcome

Python package импортируется, lock воспроизводим; Ruff/MyPy проверяют поддерживаемые модули.

## Preconditions

Зависимости: BE-007. Для реализации они должны быть done;
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

- Написать positive test: Python package импортируется, lock воспроизводим; Ruff/MyPy проверяют поддерживаемые модули.
- Зафиксировать negative test: Неверная версия dependency ломает lock check.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-008-POS`: Python package импортируется, lock воспроизводим; Ruff/MyPy проверяют поддерживаемые модули.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-008-NEG`: Неверная версия dependency ломает lock check.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Python package импортируется, lock воспроизводим; Ruff/MyPy проверяют поддерживаемые модули. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Неверная версия dependency ломает lock check. Изменение Outcome требует пересмотра зависимых карточек.

## Mini-plan и фактическое исполнение

BE-007 закрыта после merge PR #1. Добавить устанавливаемый src package, py.typed,
setuptools build metadata, проверку installed versions по lock и isolated-import test.
API/DB impact отсутствует. Сначала import test получил ModuleNotFoundError;
после реализации проверяются installed distribution metadata и typed marker из temp directory.
Отрицательный тест подменяет pin Pydantic на 0.0.0 и требует отказ проверки lock.
Задача in_review до CI и merge своего PR.

Merged PR #2: `17f6917`; head `ab78556`, [CI success](https://github.com/Salyukovgleb/FORMA/actions/runs/41083987291). 13 tests, lint/types/lock/schema green.
