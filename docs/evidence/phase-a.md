# Evidence фазы A

Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-001–007, [review](../ARCHITECTURAL_REVIEW.md).

Фактически выполнено: design DDL и примеры 14 таблиц на отдельной временной PostgreSQL
14.19; 10 отрицательных integrity сценариев прошли. Временный кластер остановлен и удалён.
Пользовательская БД и volumes не использовались.

Первый проход contract suite обнаружил invalid OpenAPI generic names и недетерминированный
порядок JSON; причины исправлены. Итоговые результаты проверок и Git/CI добавляются после запуска.
Продуктовые migration/API/security/PDF/DOCX/backup проверки не выполнялись: реализации нет.

## Итог локальных проверок

`make ci-local` завершился с exit 0:

- Ruff: 5 файлов соответствуют format; lint passed.
- Strict MyPy: no issues in Pydantic DTO source.
- pytest: 11 passed (OpenAPI, regeneration drift, DTO examples/negative inputs, 52-task DAG,
  endpoint traceability, Markdown links, dictionary coverage).
- PostgreSQL 14.19: DDL + fixtures всех 14 таблиц + 10 отрицательных integrity сценариев passed.
- `git diff --check`: exit 0.

CI workflow проверяет эти же команды и PostgreSQL 16.6 в service container. Результат
GitHub Actions фиксируется отдельно после push; локальный green не заменяет remote evidence.
