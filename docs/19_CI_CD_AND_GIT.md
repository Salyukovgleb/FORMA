# Git и CI

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

Обязательный цикл: первая ready задача без незавершённых depends_on → чтение contracts/ADR →
feature branch feat/BE-xxx-topic → mini-plan → meaningful tests first → scoped code → docs →
локальные проверки → git diff --check + staged secret review → Conventional Commit → push → PR →
проверка CI для точного SHA → review/merge согласно protection → evidence и done.
При красной проверке задача не done; при remote недоступности remote_blocked + команда.
Не force push, не обходить branch protection, не смешивать независимые крупные изменения.
Текущая фаза A — один связный review спецификации BE-001…007; не семь фиктивно законченных features.

Фаза A workflow выполняет только реальные lint/types/docs-contract/schema проверки.
В BE-013 расширить обязательными jobs: lint, types, unit-tests, integration-tests (PostgreSQL),
migration-check (Alembic drift+seeded upgrade), security-tests, docker-build, docs-contract.
Не создавать зелёные placeholder jobs вместо отсутствующих тестов.

main и pull_request используют одинаковые checks. permissions contents:read; timeout 10m,
concurrency отменяет устаревший run ветки. Dependencies lock с hashes, pip cache по lock;
fork PR не получает secrets. Production deploy/tag только BE-052, не автоматически с push.
Branch protection настраивается администратором: PR required, актуальные checks required,
no force push/deletion, review согласно команде. CODEOWNERS не добавлен: один разработчик,
внешние reviewer usernames не заданы. Защита не считается включённой без проверки API.
