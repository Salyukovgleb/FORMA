# План миграций

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

| Revision | Задача | Upgrade | Безопасный rollback |
|---|---|---|---|
| 0001_identity | BE-011,014–015 | users/sessions/used tokens/rate buckets | На пустой тестовой БД downgrade; с данными backup и forward fix |
| 0002_projects_access | BE-019,023 | projects без main FK, members | До пользовательских данных обратим; далее запрет DROP |
| 0003_nodes_revisions | BE-025,029 | nodes/revisions, затем nullable main composite FK и triggers | Сначала убрать FK/trigger; production только restore/forward fix |
| 0004_snapshots_jobs | BE-031,033 | snapshots/entries/jobs/logs | Drain jobs; backup; не удалять retained данные |
| 0005_artifacts_audit | BE-035,046 | artifacts/audit | Не терять audit; forward fix |

DDL — целевая схема, не готовая Alembic revision. Typed SQLAlchemy модели появятся в
BE-011/014/019/025/031; сейчас продуктовые ORM исходники намеренно не реализуются.
Autogenerate требует ревью: partial indexes, triggers, CHECK и deferred FK проверять вручную.
Migration gate: fresh upgrade; upgrade N−1 с seeded пользователями/папками/revisions/jobs;
проверка count/hash/FK; повторный upgrade; Alembic check; downgrade/upgrade только disposable DB.
Не делать автоматический downgrade при ошибке релиза с пользовательскими данными.

Миграции выполняет один отдельный процесс до старта новой API/worker версии. Роль runtime
не имеет DDL; migrator имеет CREATE/ALTER. Expand/backfill/validate/contract для будущих
NOT NULL/rename; backfill батчами, nullable совместимость одного релиза. Согласованный backup
обязателен до destructive изменения; восстановление на отдельную БД с проверкой blob manifest.
