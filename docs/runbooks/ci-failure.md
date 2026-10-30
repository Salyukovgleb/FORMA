# Runbook: ci-failure

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](../tasks/ROADMAP.md).

`gh pr checks` показывает failing check; `gh run view RUN_ID --log-failed` — причину.
Сопоставить head SHA с локальным `git rev-parse HEAD`. Воспроизвести соответствующий Make target,
исправить причину, обновить docs/contracts если менялся API, новый commit/push, дождаться green.
Не скрывать failure skip/continue-on-error. Network outage — remote_blocked, не done.
Фаза A локально `make ci-local`; product checks будут добавлены в BE-013.
