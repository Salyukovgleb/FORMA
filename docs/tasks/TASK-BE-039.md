---
id: "BE-039"
title: "Поддерживаемое LaTeX subset, DOCX compatibility matrix, набор fixtures"
epic: "EPIC-06"
priority: "P0"
status: "in_review"
depends_on: ["BE-007"]
owner: "backend-developer"
estimate: "0.5–2 developer days"
requirements: ["FR-DOC-002", "FR-DOC-003"]
api: []
database: []
tests: ["BE-039-POS", "BE-039-NEG"]
adr: ["0001-modular-monolith", "0004-isolated-document-processing"]
---

# BE-039 — Поддерживаемое LaTeX subset, DOCX compatibility matrix, набор fixtures

Владелец: backend-developer. Документ: draft. Обновлено: 2026-10-30.

## Context

Поддерживаемое LaTeX subset, DOCX compatibility matrix, набор fixtures. Требования: FR-DOC-002, FR-DOC-003. Цель — следующий проверяемый инкремент milestone M5.

## Outcome

Fixtures покрывают все строки DOCX matrix, включая unsupported constructs.

## Preconditions

Зависимости: BE-007. Для реализации они должны быть done;
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

- Написать positive test: Fixtures покрывают все строки DOCX matrix, включая unsupported constructs.
- Зафиксировать negative test: Custom macros с warning.
- Реализовать только Outcome с UoW, typed ports и явными error codes.
- Обновить связанный контракт и доказательство проверок.

## Required tests

`BE-039-POS`: Fixtures покрывают все строки DOCX matrix, включая unsupported constructs.
Endpoint tests: Не применимо: задача проверяется своим POS/NEG сценарием.
Тесты реализации planned; не заменять assertions пустыми тестами.

## Negative tests

`BE-039-NEG`: Custom macros с warning.
При операции с данными проверить rollback и отсутствие частичных изменений;
при auth/ACL операции проверить другого пользователя; при I/O — отказ зависимости.

## Acceptance criteria

Fixtures покрывают все строки DOCX matrix, включая unsupported constructs. Проверка NEG воспроизводима; green локальные проверки и CI для commit SHA;
поведение совпадает с DTO/DDL/ACL; нет незакрытого critical security дефекта.

## Documentation updates

Обновить соответствующий нумерованный документ, endpoint registry при API impact,
DB dictionary при schema impact, [STATUS](STATUS.md) и CHANGELOG для значимого изменения.

## Git/CI checklist

Feature branch → meaningful tests → scoped implementation → lint/types/relevant suites →
diff/secret review → Conventional Commit → push → PR → green SHA checks → required review/merge.
До merge статус не done. Никаких force push, skip checks или удаления volumes.

## Evidence/results

18 source cases и manifest реализованы; [evidence](../evidence/BE-039.md). До merge — in_review.

## Risks

Custom macros с warning. Изменение Outcome требует пересмотра зависимых карточек.

## Mini-plan / dependency review — 2026-11-01

После BE-020 выбран первый фактически ready task BE-039; BE-007 done, остальные
project tasks BE-023/025 пока planned. Это начало задачи, не evidence готового exporter.
Изучены docs/13_DOCX_EXPORT.md, requirements FR-DOC-002/003, ADR-0004/0005,
module boundaries и threat/test strategy. API/DB/migration changes не нужны.

Outcome ограничен versioned source fixtures и supported/unsupported expectations.
Не запускать TeX/Pandoc/OOXML parsers на host: exporter/normalizer/sandbox — BE-040/041/042/034.
Ни fixtures, ни static manifest validation не доказывают editable DOCX или sandbox security.

Предполагаемые файлы: tests/fixtures/docx/manifest.json, отдельные case directories с .tex
и минимальными локальными assets, docs/13_DOCX_EXPORT.md (stable case IDs),
tests/contracts/test_docx_fixtures.py. Runtime conversion module создавать только при реальном
application Outcome, без пустого skeleton. Новых dependencies/services не добавлять.

Tests first: matrix coverage, уникальные case IDs, существующие UTF-8 sources и assets,
relative manifest paths/no traversal/symlinks, корректные support levels/warning codes,
expected OOXML structural assertions для всех поддержанных строк. Unsupported custom macro
обязан иметь location + DOCX_UNSUPPORTED_CONSTRUCT expectation, а не обещание conversion.
Отдельно покрыть multicolumn/multirow/longtable, TikZ/PSTricks/custom macros и Heading1–3.
PNG/JPEG/PDF assets с лицензированным/собственным минимальным содержимым; никакого network fetch.
Golden assertions проверятся реальным isolated exporter в BE-040/042; сейчас только corpus
integrity и полнота matrix. После реализации: tests→commit→push→PR→green SHA CI→merge.

Следующий шаг: сначала meaningful manifest/matrix tests, затем corpus. Fixtures и новые
тесты пока отсутствуют; BE-039 не done. M2 и M5 остаются открытыми.
