# Runbook: compilation-debug

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](../tasks/ROADMAP.md).

Использовать fixture snapshot без пользовательских secrets. Проверить engine/image digest,
main_path и manifest hashes. Смотреть bounded structured logs; line=null не угадывать.
Воспроизвести через тот же sandbox, не запускать недоверенный tex на host shell.
Для timeout проверить memory/PID/tmpfs limits и container exit code; не включать shell escape
или network ради диагностики. Минимизировать failing source и добавить regression fixture.
