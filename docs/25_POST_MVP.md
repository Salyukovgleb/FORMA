# Post-MVP

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

CRDT/OT совместное посимвольное редактирование, visual editor, AI помощник, OAuth,
приглашения по email, account recovery email, advanced diff, ownership transfer,
user reference.docx и сложные LaTeX handlers рассматриваются после измерений MVP.
Отдельные таблицы/службы под них сейчас не проектируются.

Multi-host storage, object store, отдельный broker, Kubernetes требуют ADR по измеренному
bottleneck, бюджету эксплуатации и плану миграции локальных keys. Усиление sandbox VM
нужно при недопустимом shared-kernel risk; текущее решение не делает такой риск нулевым.
