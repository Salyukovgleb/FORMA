# Участие в разработке

Владелец: backend-developer. Статус: draft. Обновлено: 2026-10-30. Связи: BE-007/013.

Работа идёт по [карточкам](docs/tasks/README.md), по одной задаче с закрытыми dependencies.
[AGENTS](AGENTS.md) содержит обязательный tests→commit→push→CI→review протокол.
Перед PR выполнить `make ci-local`, `git diff --check`; приложить точные результаты и SHA.
Для API менять models.py/registry.py, выполнить make contracts и проверить diff.
Для БД менять design SQL/dictionary и, после M1, Alembic вместе с data migration tests.

Conventional Commit: `feat(files): add revision-safe save (BE-027)`;
для проектирования `docs: specify phase A architecture (BE-001–007)`.
Не отправлять .env, .venv, database dumps, пользовательские blobs и секреты в Git.
Локальный green не равен CI green или merge; статусы отражаются отдельно.
