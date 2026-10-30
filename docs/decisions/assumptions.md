# Допущения

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](../tasks/ROADMAP.md).

| ID | Решение | Проверка |
|---|---|---|
| A-001 | Один Linux host, local persistent volume | ADR-0002, BE-009/047 |
| A-002 | Frontend same-site, separate team | ADR-0006, BE-018 |
| A-003 | Только registered user sharing | BE-023 |
| A-004 | Optimistic locking без realtime | BE-027/030 |
| A-005 | Templates/reference versioned seeds | BE-021/040 |
| A-006 | Rootless cgroup v2 production host | BE-034 fail-closed self-test |
| A-007 | Retention 7/30/90 и quotas как в NFR | ADR-0007, BE-048 |
| A-008 | После reload нужен login; silent refresh вне MVP | ADR-0006, frontend acceptance |

Допущения конкретны и приняты для draft; изменение требует ADR/контрактного review,
не оставлено на усмотрение реализации. Production host фактически ещё не проверен.
