---
id: "BE-013"
title: "GitHub Actions: lint, types, unit/integration, migration, build"
epic: "EPIC-01"
priority: "P0"
status: "done"
depends_on: ["BE-009", "BE-011", "BE-012"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["NFR-OPS-001"]
api: []
database: []
tests: ["BE-013-POS", "BE-013-NEG"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-013 — GitHub Actions: lint, types, unit/integration, migration, build

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

GitHub Actions: lint, types, unit/integration, migration, build. Требования: NFR-OPS-001. Цель — следующий проверяемый инкремент milestone M1.

## Outcome

Обязательные lint/types/unit/integration/migration/security/build/docs checks реально выполняются.

## Preconditions

Зависимости: BE-009, BE-011, BE-012. Для реализации они должны быть done;
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

- Написать positive test: Обязательные lint/types/unit/integration/migration/security/build/docs checks реально выполняются.
- Зафиксировать negative test: Отсутствующий test suite не зелёный placeholder.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-013-POS`: Обязательные lint/types/unit/integration/migration/security/build/docs checks реально выполняются.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-013-NEG`: Отсутствующий test suite не зелёный placeholder.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Обязательные lint/types/unit/integration/migration/security/build/docs checks реально выполняются. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
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

Отсутствующий test suite не зелёный placeholder. Изменение Outcome требует пересмотра зависимых карточек.

ADR-0008 integration gate: Проверять API/DB Docker images; worker smoke добавляется после BE-032.

## Mini-plan / evidence

BE-009/011/012 merged. Восемь отдельных checks с одним locked Python setup composite action.
PostgreSQL service только integration/migration checks, Docker smoke отдельным job.
Policy test сначала падал на отсутствующих шести gates. После реализации local green:
required names, unconditional checks, read-only token, bounded timeout, pinned external actions,
без continue-on-error/ignored failures/secrets. Dependency graph проверяется pip check,
версии/hashes — locks. Это не CVE scan; release security review BE-049 остаётся обязательным.
Security baseline — config/logging/HTTP (18 реальных tests), не выдуманные auth/ACL tests.
После BE-014–018/023/034 security gate расширяется новыми suites без placeholders/skips.

Merged [PR #10](https://github.com/Salyukovgleb/FORMA/pull/10), `a49b27680d0ee1ec1167e4363a8a5acce362b93b`. [CI bf27908](https://github.com/Salyukovgleb/FORMA/actions/runs/41198323122): все8 checks SUCCESS. BE-013 done.
