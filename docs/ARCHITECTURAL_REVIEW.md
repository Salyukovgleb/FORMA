# Architectural Review — фаза A

Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-001–007; ADR-0001–0007; [evidence](evidence/phase-a.md).

Спроектирован модульный монолит, 14 таблиц, 46 planned API методов, 52 задачи.
Продуктовых routes, ORM, миграций и worker пока нет. Созданы исполняемые проектные DTO,
DDL, генератор OpenAPI и проверки документации. Это технический self-review, не approval
продуктовой готовности и не проверка runtime security.

| Проверенная связка | Решение / результат |
|---|---|
| endpoint → DTO → examples | Canonical registry и Pydantic; генератор проверяется на drift |
| endpoint → ACL → DB → tests → tasks | endpoints.json; все IDs разрешаются |
| owner invariant | Единственный projects.owner_id; owner не membership role |
| main_file / node project | Composite deferred FK + live .tex trigger |
| revision semantics | Metadata revision отделена от content revision; save409 |
| file publication / DB rollback | Immutable publish first; unreachable orphan; protected GC |
| snapshot / concurrent edits | DB snapshot entries pin immutable revisions |
| expired worker / duplicate output | Lease token fenced terminal commit; kill old attempt before retry |
| cancellation / publication | Job lock определяет победивший commit |
| auth revocation / JWT | Session проверяется каждый request; refresh history detects replay |
| backup / live writes | Exclusive maintenance barrier, writers paused |
| jobs / quota | Lock users in UUID order → project → node/job; scheduler lock при claim |
| task dependency graph | Ацикличный; числовой порядок не равен порядку исполнения |

Исправления self-review: generic Pydantic Page names нормализованы для OpenAPI component keys;
генерация JSON детерминирована; warnings включены в Job DTO; запрещено объявлять пять
последовательно зависимых задач одновременно ready. Точные результаты запусков — evidence.

Release blockers: реальный Linux sandbox, rootless cgroup delegation, DOCX fidelity на
fixtures, restore rehearsal и account recovery policy. Они имеют конкретные задачи и
не считаются закрытыми этим review. Deployment не разрешён по результатам одной фазы A.

M0 specification review подготовлен. Документы остаются draft, BE-001…007 in_review до
PR/review/merge. Следующий implementation gate — BE-008 после закрытия M0; фазу B здесь не начинать.

GitHub main фактически не защищена (`protected=false`); настройка required checks и review
остаётся обязанностью администратора до implementation merges. PR #1 открыт; self-merge не выполнен.
