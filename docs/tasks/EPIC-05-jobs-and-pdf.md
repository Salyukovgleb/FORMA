# EPIC-05: Jobs and PDF

Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30. Связи: BE-001…052.

- [BE-031](TASK-BE-031.md): Таблица jobs, состояния, lease, retry policy, атомарный claim
- [BE-032](TASK-BE-032.md): Worker process, heartbeats, stale jobs, cancellation
- [BE-033](TASK-BE-033.md): Immutable project snapshot и staging на каждый job
- [BE-034](TASK-BE-034.md): Security sandbox для недоверенного LaTeX; подтверждающие тесты
- [BE-035](TASK-BE-035.md): PDF compilation adapter и сохранение артефактов
- [BE-036](TASK-BE-036.md): Parsing LaTeX logs с error/warning/file/line по возможности
- [BE-037](TASK-BE-037.md): Compile API, job status/list/logs/cancel, download
- [BE-038](TASK-BE-038.md): End-to-end тесты сборки, таймаутов, безопасности, конкурентности

Выход: все перечисленные Outcomes проверены; критические NEG сценарии зелёные.
