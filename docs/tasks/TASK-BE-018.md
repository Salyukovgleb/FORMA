---
id: "BE-018"
title: "ACL tests, session expiry/replay tests, rate limiting on auth"
epic: "EPIC-02"
priority: "P0"
status: "done"
depends_on: ["BE-016", "BE-017"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-AUTH-001", "FR-ACL-001"]
api: []
database: ["rate_limit_buckets", "auth_sessions", "used_refresh_tokens", "users"]
tests: ["BE-018-POS", "BE-018-NEG"]
adr: ["0001-modular-monolith", "0002-local-filesystem-storage"]
---

# BE-018 — ACL tests, session expiry/replay tests, rate limiting on auth

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

ACL tests, session expiry/replay tests, rate limiting on auth. Требования: FR-AUTH-001, FR-ACL-001. Цель — следующий проверяемый инкремент milestone M1.

## Outcome

Auth rate limits атомарны; expired/replayed/revoked sessions отвергаются.

## Preconditions

Зависимости: BE-016, BE-017. Для реализации они должны быть done;
текущее наличие draft не означает закрытую зависимость. Прочитать [архитектуру](../02_ARCHITECTURE.md),
[API registry](../contracts/endpoints.json), [threat model](../16_SECURITY_THREAT_MODEL.md).

## Files to change

`src/forma_backend/modules/identity/`; соответствующие tests/integration/,
[STATUS](STATUS.md), связанные API docs и migration plan при изменении схемы.
Точный список новых файлов зафиксировать в mini-plan перед реализацией; пустые skeletons не добавлять.

## API/DB impacts

Методы: Публичный endpoint не добавляется этой задачей.
Таблицы API: Схема/инфраструктурный impact определяется Outcome; целевой DDL в database/schema.sql.
Breaking wire changes запрещены без обновления OpenAPI/ADR. Новые DB объекты — Alembic revision.

## Implementation checklist

- Написать positive test: Auth rate limits атомарны; expired/replayed/revoked sessions отвергаются.
- Зафиксировать negative test: Burst на границе rate window.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-018-POS`: Auth rate limits атомарны; expired/replayed/revoked sessions отвергаются.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-018-NEG`: Burst на границе rate window.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Auth rate limits атомарны; expired/replayed/revoked sessions отвергаются. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
поведение совпадает с DTO/DDL/ACL; нет незакрытого critical security дефекта.

## Documentation updates

Обновить соответствующий нумерованный документ, endpoint registry при API impact,
DB dictionary при schema impact, [STATUS](STATUS.md) и CHANGELOG для значимого изменения.

## Git/CI checklist

Feature branch → meaningful tests → scoped implementation → lint/types/relevant suites →
diff/secret review → Conventional Commit → push → PR → green SHA checks → required review/merge.
До merge статус не done. Никаких force push, skip checks или удаления volumes.

## Evidence/results

Локальные checks passed; [evidence](../evidence/BE-018.md). PR #17 merged `bf37ba2`, восемь checks SUCCESS для head `c8a2b4c`.

## Risks

Burst на границе rate window. Изменение Outcome требует пересмотра зависимых карточек.

## Mini-plan — 2026-10-31

BE-016/017 done, BE-018 ready → in_progress. Policy regression в security suite уже есть;
expiry/replay/revocation tests сохраняются. Новый tests/integration/test_auth_limits.py:
24 concurrent same-subject attempts без потерянных increments; два deterministic соседних
окна (DB clock expression controlled только в test harness), долгоживущая transaction,
реальный login IP/email limits и refresh30/min с committed429 и непродлённой session.
Воспроизвести выбор старого rate window через transaction now(), затем использовать
statement_timestamp() — серверное время текущего SQL statement.
Rate buckets старше24h: ограниченная cleanup-функция и отдельная operator CLI/Make target;
SKIP LOCKED, max rows, rollback-safe и timeouts; автоматический scheduler не добавляется.
Files: infrastructure/identity/rate_limit.py, infrastructure/identity/cleanup_limits.py,
новый test suite, Makefile, auth/NFR/runbook/evidence. Без новых routes/schema/dependencies.
