# API: access

Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30. Состояние реализации указано для каждого метода.

## API-034 — ListMembers

`GET /api/v1/projects/{project_id}/members` · implemented · operationId `list_members` · tag `access`.

Назначение и транзакция: Owner из projects плюс editor/viewer из project_members; максимум 50.

Авторизация: `reader`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[
  {
    "in": "path",
    "name": "project_id",
    "required": true,
    "schema": {
      "format": "uuid",
      "type": "string"
    }
  }
]
```

Запрос — `none`:

Тело отсутствует.

Успех HTTP 200 — `Members`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `items` | `{"items": {"$ref": "#/components/schemas/Member"}, "title": "Items", "type": "array"}` | True |

Пример:
```json
{
  "items": []
}
```

Ошибки: 400, 401, 403, 404, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: users, auth_sessions, projects, project_members; planned BE-046 audit будет добавлять event `list_members`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-034` — правило use case; `API-034` — happy path и DTO;
`INT-API-034` — транзакция/rollback и конфликт; `SEC-API-034` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-023](../tasks/TASK-BE-023.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-035 — GrantProjectAccess

`POST /api/v1/projects/{project_id}/members` · implemented · operationId `grant_project_access` · tag `access`.

Назначение и транзакция: Lock project; active normalized email; unknown404 USER_NOT_FOUND, owner409 OWNER_IMMUTABLE, duplicate409 MEMBER_EXISTS,50 total cap429 MEMBER_LIMIT_EXCEEDED.

Авторизация: `owner`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[
  {
    "in": "path",
    "name": "project_id",
    "required": true,
    "schema": {
      "format": "uuid",
      "type": "string"
    }
  }
]
```

Запрос — `MemberAdd`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `email` | `{"maxLength": 254, "minLength": 3, "pattern": "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$", "title": "Email", "type": "string"}` | True |
| `role` | `{"enum": ["editor", "viewer"], "title": "Role", "type": "string"}` | True |

Пример:
```json
{
  "email": "user@example.org",
  "role": "editor"
}
```

Успех HTTP 201 — `Member`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `user_id` | `{"format": "uuid", "title": "User Id", "type": "string"}` | True |
| `display_name` | `{"title": "Display Name", "type": "string"}` | True |
| `role` | `{"enum": ["owner", "editor", "viewer"], "title": "Role", "type": "string"}` | True |
| `created_at` | `{"format": "date-time", "title": "Created At", "type": "string"}` | True |

Пример:
```json
{
  "created_at": "2026-10-30T12:00:00Z",
  "display_name": "x",
  "role": "owner",
  "user_id": "11111111-1111-4111-8111-111111111111"
}
```

Ошибки: 400, 401, 403, 404, 409, 413, 415, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: users, auth_sessions, projects, project_members; planned BE-046 audit будет добавлять event `grant_project_access`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-035` — правило use case; `API-035` — happy path и DTO;
`INT-API-035` — транзакция/rollback и конфликт; `SEC-API-035` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-023](../tasks/TASK-BE-023.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-036 — ChangeMemberRole

`PATCH /api/v1/projects/{project_id}/members/{user_id}` · implemented · operationId `change_member_role` · tag `access`.

Назначение и транзакция: Lock project; role editor/viewer; owner неизменяем, попытка 409 OWNER_IMMUTABLE.

Авторизация: `owner`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[
  {
    "in": "path",
    "name": "project_id",
    "required": true,
    "schema": {
      "format": "uuid",
      "type": "string"
    }
  },
  {
    "in": "path",
    "name": "user_id",
    "required": true,
    "schema": {
      "format": "uuid",
      "type": "string"
    }
  }
]
```

Запрос — `MemberPatch`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `role` | `{"enum": ["editor", "viewer"], "title": "Role", "type": "string"}` | True |

Пример:
```json
{
  "role": "editor"
}
```

Успех HTTP 200 — `Member`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `user_id` | `{"format": "uuid", "title": "User Id", "type": "string"}` | True |
| `display_name` | `{"title": "Display Name", "type": "string"}` | True |
| `role` | `{"enum": ["owner", "editor", "viewer"], "title": "Role", "type": "string"}` | True |
| `created_at` | `{"format": "date-time", "title": "Created At", "type": "string"}` | True |

Пример:
```json
{
  "created_at": "2026-10-30T12:00:00Z",
  "display_name": "x",
  "role": "owner",
  "user_id": "11111111-1111-4111-8111-111111111111"
}
```

Ошибки: 400, 401, 403, 404, 409, 413, 415, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: users, auth_sessions, projects, project_members; planned BE-046 audit будет добавлять event `change_member_role`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-036` — правило use case; `API-036` — happy path и DTO;
`INT-API-036` — транзакция/rollback и конфликт; `SEC-API-036` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-023](../tasks/TASK-BE-023.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-037 — RemoveMember

`DELETE /api/v1/projects/{project_id}/members/{user_id}` · implemented · operationId `remove_member` · tag `access`.

Назначение и транзакция: Owner может удалить участника; editor/viewer только себя; owner выйти не может; повторный вызов после потери ACL 404.

Авторизация: `owner_or_self`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[
  {
    "in": "path",
    "name": "project_id",
    "required": true,
    "schema": {
      "format": "uuid",
      "type": "string"
    }
  },
  {
    "in": "path",
    "name": "user_id",
    "required": true,
    "schema": {
      "format": "uuid",
      "type": "string"
    }
  }
]
```

Запрос — `none`:

Тело отсутствует.

Успех HTTP 204 — `none`:

Тело отсутствует.

Ошибки: 400, 401, 403, 404, 409, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: users, auth_sessions, projects, project_members; planned BE-046 audit будет добавлять event `remove_member`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-037` — правило use case; `API-037` — happy path и DTO;
`INT-API-037` — транзакция/rollback и конфликт; `SEC-API-037` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-023](../tasks/TASK-BE-023.md),
[ADR-0001](../adr/0001-modular-monolith.md).
