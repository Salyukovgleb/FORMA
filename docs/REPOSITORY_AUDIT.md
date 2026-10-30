# Аудит исходного состояния FORMA

Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-001; [архитектура](02_ARCHITECTURE.md); [допущения](decisions/assumptions.md).

На момент первого осмотра `/Users/salyukov.gleb033icloud.com/Documents/Repos/INFRA`
был пустым каталогом: отсутствовали исходники, Git, миграции, тесты, CI,
Docker Compose, конфигурация и инструкции AGENTS.md в родительских каталогах.
Существующие пользовательские исходники не удалялись.

По прямому запросу пользователя создан Git и первый коммит `08d4e9d`.
После следующего запроса origin заменён на https://github.com/Salyukovgleb/FORMA.git.
GitHub CLI подтвердил имя FORMA; push main выполнен успешно. Это не проверка CI.
Старый удалённый репозиторий через GitHub API не удалялся.

Локально создана исключённая из Git `.venv`; подтверждён импорт Pydantic 2.12.3.
Наличие Docker CLI подтверждено, работоспособность daemon пока не установлена.
В `docs/contracts/models.py` определены DTO для 46 planned методов: это проектные контракты, не работающий API.
SQLAlchemy, Alembic, HTTP routes, worker, sandbox и продуктовые тесты отсутствуют.

## Ограничения и последствия

- Нет legacy-схемы: миграции проектируются с нуля; тесты миграций на данных всё равно обязательны.
- Единственный локальный том исключает независимое масштабирование API по разным хостам.
- Система исполнения TeX требует отдельной проверяемой границы безопасности.
- Производительность, совместимость Word, восстановление и изоляция пока не измерены.
- Пакет M0 подготовлен для review: SQL, словарь, endpoint registry, DAG и проверки находятся в docs/; approval/merge ещё нет.

## Доказательства

Фактически выполнены: `git status`, `git remote -v`, `git ls-remote origin refs/heads/main`,
`gh repo view Salyukovgleb/FORMA --json name,url`, `git push -u origin main`.
Продуктовые тесты, Alembic migrations, runtime build и merge документации не выполнены. Актуальные результаты design SQL и GitHub Actions см. [evidence](evidence/phase-a.md).
