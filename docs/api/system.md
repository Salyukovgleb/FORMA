# API: system

Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30. Реализация: planned.

## API-001 — Liveness

`GET /health/live` · planned · operationId `liveness` · tag `system`.

Назначение и транзакция: Без I/O; проверка event loop.

Авторизация: `public`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[]
```

Запрос — `none`:

Тело отсутствует.

Успех HTTP 200 — `Health`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `status` | `{"enum": ["ok", "unavailable"], "title": "Status", "type": "string"}` | True |

Пример:
```json
{
  "status": "ok"
}
```

Ошибки: 400, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: нет; mutation добавляет audit event `liveness`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-001` — правило use case; `API-001` — happy path и DTO;
`INT-API-001` — транзакция/rollback и конфликт; `SEC-API-001` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-012](../tasks/TASK-BE-012.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-002 — Readiness

`GET /health/ready` · planned · operationId `readiness` · tag `system`.

Назначение и транзакция: SELECT 1 и пробная запись/удаление отдельного health-файла; timeout 2s, иначе 503.

Авторизация: `public`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[]
```

Запрос — `none`:

Тело отсутствует.

Успех HTTP 200 — `Health`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `status` | `{"enum": ["ok", "unavailable"], "title": "Status", "type": "string"}` | True |

Пример:
```json
{
  "status": "ok"
}
```

Ошибки: 400, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: нет; mutation добавляет audit event `readiness`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-002` — правило use case; `API-002` — happy path и DTO;
`INT-API-002` — транзакция/rollback и конфликт; `SEC-API-002` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-012](../tasks/TASK-BE-012.md),
[ADR-0001](../adr/0001-modular-monolith.md).
