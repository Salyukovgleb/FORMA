# Runbook: failed-job

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](../tasks/ROADMAP.md).

Оператор получает job_id/request_id из безопасного log. Проверить state/attempt/lease,
container labels и действующий ACL requester. Source errors вернуть пользователю с diagnostics;
не retry вручную. Expired lease: остановить exact old attempt container, подтвердить exit,
затем дать reaper провести fenced transition. Если daemon недоступен — блокировать новые claims.
Не менять succeeded обратно в queued. Новая ручная сборка — новый API request/key после исправления.
При orphan artifact не удалять файл вручную; GC проверяет references и grace period.
