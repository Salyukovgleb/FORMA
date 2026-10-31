# EPIC-02: Identity

Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30. Связи: BE-001…052.

- [BE-014](TASK-BE-014.md): Модель users, безопасная регистрация, хеширование паролей
- [BE-015](TASK-BE-015.md): Login, refresh rotation, logout, session revocation
- [BE-016](TASK-BE-016.md): Profile read/update и смена пароля
- [BE-017](TASK-BE-017.md): Role policy owner/editor/viewer, object-level authorization
- [BE-018](TASK-BE-018.md): ACL tests, session expiry/replay tests, rate limiting on auth

Выход: все перечисленные Outcomes проверены; критические NEG сценарии зелёные.

BE-014…018 merged и verified (PR #12/#13/#14/#16/#17), ссылки на SHA/CI — STATUS/evidence.
Role policy verified отдельно; project repository/HTTP integration выполняется следующими
задачами. Общие API quotas/automatic retention ещё planned; M2 включает также BE-019…023.
