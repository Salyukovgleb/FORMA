# API: projects

Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30. Состояние реализации указано для каждого метода.

## API-013 — ListProjects

`GET /api/v1/projects` · planned · operationId `list_projects` · tag `projects`.

Назначение и транзакция: Доступные active проекты; status=deleted показывает только собственные удалённые.

Авторизация: `authenticated`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[
  {
    "in": "query",
    "name": "limit",
    "schema": {
      "default": 50,
      "maximum": 100,
      "minimum": 1,
      "type": "integer"
    }
  },
  {
    "in": "query",
    "name": "cursor",
    "schema": {
      "maxLength": 2048,
      "type": "string"
    }
  },
  {
    "in": "query",
    "name": "q",
    "schema": {
      "maxLength": 200,
      "type": "string"
    }
  },
  {
    "in": "query",
    "name": "status",
    "schema": {
      "default": "active",
      "enum": [
        "active",
        "deleted"
      ],
      "type": "string"
    }
  }
]
```

Запрос — `none`:

Тело отсутствует.

Успех HTTP 200 — `Page_Project_`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `items` | `{"items": {"$ref": "#/components/schemas/Project"}, "title": "Items", "type": "array"}` | True |
| `next_cursor` | `{"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Next Cursor"}` | True |

Пример:
```json
{
  "items": [],
  "next_cursor": "x"
}
```

Ошибки: 400, 401, 403, 404, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: projects, project_members, project_nodes; planned BE-046 audit будет добавлять event `list_projects`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-013` — правило use case; `API-013` — happy path и DTO;
`INT-API-013` — транзакция/rollback и конфликт; `SEC-API-013` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-020](../tasks/TASK-BE-020.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-014 — CreateProject

`POST /api/v1/projects` · implemented · operationId `create_project` · tag `projects`.

Назначение и транзакция: Maintenance shared guard; lock user/session; quota retained projects; INSERT own empty project. template_id не null пока404 (BE-021). Audit — BE-046.

Авторизация: `authenticated`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[]
```

Запрос — `ProjectCreate`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `title` | `{"maxLength": 200, "minLength": 1, "title": "Title", "type": "string"}` | True |
| `description` | `{"default": "", "maxLength": 2000, "title": "Description", "type": "string"}` | False |
| `template_id` | `{"anyOf": [{"maxLength": 128, "minLength": 1, "type": "string"}, {"type": "null"}], "default": null, "title": "Template Id"}` | False |

Пример:
```json
{
  "description": "",
  "template_id": null,
  "title": "x"
}
```

Успех HTTP 201 — `Project`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `id` | `{"format": "uuid", "title": "Id", "type": "string"}` | True |
| `owner_id` | `{"format": "uuid", "title": "Owner Id", "type": "string"}` | True |
| `title` | `{"title": "Title", "type": "string"}` | True |
| `description` | `{"title": "Description", "type": "string"}` | True |
| `role` | `{"enum": ["owner", "editor", "viewer"], "title": "Role", "type": "string"}` | True |
| `status` | `{"enum": ["active", "deleted"], "title": "Status", "type": "string"}` | True |
| `revision` | `{"minimum": 1, "title": "Revision", "type": "integer"}` | True |
| `created_at` | `{"format": "date-time", "title": "Created At", "type": "string"}` | True |
| `updated_at` | `{"format": "date-time", "title": "Updated At", "type": "string"}` | True |
| `deleted_at` | `{"anyOf": [{"format": "date-time", "type": "string"}, {"type": "null"}], "title": "Deleted At"}` | True |

Пример:
```json
{
  "created_at": "2026-10-30T12:00:00Z",
  "deleted_at": "2026-10-30T12:00:00Z",
  "description": "x",
  "id": "11111111-1111-4111-8111-111111111111",
  "owner_id": "11111111-1111-4111-8111-111111111111",
  "revision": 1,
  "role": "owner",
  "status": "active",
  "title": "x",
  "updated_at": "2026-10-30T12:00:00Z"
}
```

Ошибки: 400, 401, 403, 404, 409, 413, 415, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: users, auth_sessions, projects; planned BE-046 audit будет добавлять event `create_project`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-014` — правило use case; `API-014` — happy path и DTO;
`INT-API-014` — транзакция/rollback и конфликт; `SEC-API-014` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-019](../tasks/TASK-BE-019.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-015 — ReadProject

`GET /api/v1/projects/{project_id}` · planned · operationId `read_project` · tag `projects`.

Назначение и транзакция: SELECT проекта и вычисленной роли; deleted доступен только owner.

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

Успех HTTP 200 — `Project`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `id` | `{"format": "uuid", "title": "Id", "type": "string"}` | True |
| `owner_id` | `{"format": "uuid", "title": "Owner Id", "type": "string"}` | True |
| `title` | `{"title": "Title", "type": "string"}` | True |
| `description` | `{"title": "Description", "type": "string"}` | True |
| `role` | `{"enum": ["owner", "editor", "viewer"], "title": "Role", "type": "string"}` | True |
| `status` | `{"enum": ["active", "deleted"], "title": "Status", "type": "string"}` | True |
| `revision` | `{"minimum": 1, "title": "Revision", "type": "integer"}` | True |
| `created_at` | `{"format": "date-time", "title": "Created At", "type": "string"}` | True |
| `updated_at` | `{"format": "date-time", "title": "Updated At", "type": "string"}` | True |
| `deleted_at` | `{"anyOf": [{"format": "date-time", "type": "string"}, {"type": "null"}], "title": "Deleted At"}` | True |

Пример:
```json
{
  "created_at": "2026-10-30T12:00:00Z",
  "deleted_at": "2026-10-30T12:00:00Z",
  "description": "x",
  "id": "11111111-1111-4111-8111-111111111111",
  "owner_id": "11111111-1111-4111-8111-111111111111",
  "revision": 1,
  "role": "owner",
  "status": "active",
  "title": "x",
  "updated_at": "2026-10-30T12:00:00Z"
}
```

Ошибки: 400, 401, 403, 404, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: projects, project_members, project_nodes; planned BE-046 audit будет добавлять event `read_project`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-015` — правило use case; `API-015` — happy path и DTO;
`INT-API-015` — транзакция/rollback и конфликт; `SEC-API-015` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-020](../tasks/TASK-BE-020.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-016 — UpdateProject

`PATCH /api/v1/projects/{project_id}` · planned · operationId `update_project` · tag `projects`.

Назначение и транзакция: Lock project; expected_revision; title/description; увеличить revision.

Авторизация: `writer`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
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

Запрос — `ProjectPatch`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `title` | `{"maxLength": 200, "minLength": 1, "title": "Title", "type": "string"}` | True |
| `description` | `{"maxLength": 2000, "title": "Description", "type": "string"}` | True |
| `expected_revision` | `{"minimum": 1, "title": "Expected Revision", "type": "integer"}` | True |

Пример:
```json
{
  "description": "x",
  "expected_revision": 1,
  "title": "x"
}
```

Успех HTTP 200 — `Project`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `id` | `{"format": "uuid", "title": "Id", "type": "string"}` | True |
| `owner_id` | `{"format": "uuid", "title": "Owner Id", "type": "string"}` | True |
| `title` | `{"title": "Title", "type": "string"}` | True |
| `description` | `{"title": "Description", "type": "string"}` | True |
| `role` | `{"enum": ["owner", "editor", "viewer"], "title": "Role", "type": "string"}` | True |
| `status` | `{"enum": ["active", "deleted"], "title": "Status", "type": "string"}` | True |
| `revision` | `{"minimum": 1, "title": "Revision", "type": "integer"}` | True |
| `created_at` | `{"format": "date-time", "title": "Created At", "type": "string"}` | True |
| `updated_at` | `{"format": "date-time", "title": "Updated At", "type": "string"}` | True |
| `deleted_at` | `{"anyOf": [{"format": "date-time", "type": "string"}, {"type": "null"}], "title": "Deleted At"}` | True |

Пример:
```json
{
  "created_at": "2026-10-30T12:00:00Z",
  "deleted_at": "2026-10-30T12:00:00Z",
  "description": "x",
  "id": "11111111-1111-4111-8111-111111111111",
  "owner_id": "11111111-1111-4111-8111-111111111111",
  "revision": 1,
  "role": "owner",
  "status": "active",
  "title": "x",
  "updated_at": "2026-10-30T12:00:00Z"
}
```

Ошибки: 400, 401, 403, 404, 409, 413, 415, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: projects, project_members, project_nodes; planned BE-046 audit будет добавлять event `update_project`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-016` — правило use case; `API-016` — happy path и DTO;
`INT-API-016` — транзакция/rollback и конфликт; `SEC-API-016` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-020](../tasks/TASK-BE-020.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-017 — DeleteProject

`DELETE /api/v1/projects/{project_id}` · planned · operationId `delete_project` · tag `projects`.

Назначение и транзакция: Сверить confirm_title и expected_revision; soft delete; запросить отмену jobs; retention 7 суток.

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

Запрос — `DeleteProject`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `confirm_title` | `{"title": "Confirm Title", "type": "string"}` | True |
| `expected_revision` | `{"minimum": 1, "title": "Expected Revision", "type": "integer"}` | True |

Пример:
```json
{
  "confirm_title": "x",
  "expected_revision": 1
}
```

Успех HTTP 204 — `none`:

Тело отсутствует.

Ошибки: 400, 401, 403, 404, 409, 413, 415, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: projects, project_members, project_nodes; planned BE-046 audit будет добавлять event `delete_project`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-017` — правило use case; `API-017` — happy path и DTO;
`INT-API-017` — транзакция/rollback и конфликт; `SEC-API-017` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-020](../tasks/TASK-BE-020.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-018 — RestoreProject

`POST /api/v1/projects/{project_id}/restore` · planned · operationId `restore_project` · tag `projects`.

Назначение и транзакция: До 7 суток восстановить deleted проект с проверкой revision; далее 410; активный 409.

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

Запрос — `RestoreProject`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `expected_revision` | `{"minimum": 1, "title": "Expected Revision", "type": "integer"}` | True |

Пример:
```json
{
  "expected_revision": 1
}
```

Успех HTTP 200 — `Project`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `id` | `{"format": "uuid", "title": "Id", "type": "string"}` | True |
| `owner_id` | `{"format": "uuid", "title": "Owner Id", "type": "string"}` | True |
| `title` | `{"title": "Title", "type": "string"}` | True |
| `description` | `{"title": "Description", "type": "string"}` | True |
| `role` | `{"enum": ["owner", "editor", "viewer"], "title": "Role", "type": "string"}` | True |
| `status` | `{"enum": ["active", "deleted"], "title": "Status", "type": "string"}` | True |
| `revision` | `{"minimum": 1, "title": "Revision", "type": "integer"}` | True |
| `created_at` | `{"format": "date-time", "title": "Created At", "type": "string"}` | True |
| `updated_at` | `{"format": "date-time", "title": "Updated At", "type": "string"}` | True |
| `deleted_at` | `{"anyOf": [{"format": "date-time", "type": "string"}, {"type": "null"}], "title": "Deleted At"}` | True |

Пример:
```json
{
  "created_at": "2026-10-30T12:00:00Z",
  "deleted_at": "2026-10-30T12:00:00Z",
  "description": "x",
  "id": "11111111-1111-4111-8111-111111111111",
  "owner_id": "11111111-1111-4111-8111-111111111111",
  "revision": 1,
  "role": "owner",
  "status": "active",
  "title": "x",
  "updated_at": "2026-10-30T12:00:00Z"
}
```

Ошибки: 400, 401, 403, 404, 409, 410, 413, 415, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: projects, project_members, project_nodes; planned BE-046 audit будет добавлять event `restore_project`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-018` — правило use case; `API-018` — happy path и DTO;
`INT-API-018` — транзакция/rollback и конфликт; `SEC-API-018` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-020](../tasks/TASK-BE-020.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-019 — ReadSettings

`GET /api/v1/projects/{project_id}/settings` · planned · operationId `read_settings` · tag `projects`.

Назначение и транзакция: SELECT main_file_id, engine и project revision.

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

Успех HTTP 200 — `Settings`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `main_file_id` | `{"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Main File Id"}` | True |
| `engine` | `{"enum": ["pdflatex", "xelatex", "lualatex"], "title": "Engine", "type": "string"}` | True |
| `revision` | `{"minimum": 1, "title": "Revision", "type": "integer"}` | True |

Пример:
```json
{
  "engine": "pdflatex",
  "main_file_id": "11111111-1111-4111-8111-111111111111",
  "revision": 1
}
```

Ошибки: 400, 401, 403, 404, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: projects, project_members, project_nodes; planned BE-046 audit будет добавлять event `read_settings`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-019` — правило use case; `API-019` — happy path и DTO;
`INT-API-019` — транзакция/rollback и конфликт; `SEC-API-019` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-022](../tasks/TASK-BE-022.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-020 — UpdateSettings

`PATCH /api/v1/projects/{project_id}/settings` · planned · operationId `update_settings` · tag `projects`.

Назначение и транзакция: Lock project; ожидаемая revision; main должен быть live .tex того же проекта; увеличить revision.

Авторизация: `writer`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
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

Запрос — `SettingsPatch`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `main_file_id` | `{"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Main File Id"}` | True |
| `engine` | `{"enum": ["pdflatex", "xelatex", "lualatex"], "title": "Engine", "type": "string"}` | True |
| `expected_revision` | `{"minimum": 1, "title": "Expected Revision", "type": "integer"}` | True |

Пример:
```json
{
  "engine": "pdflatex",
  "expected_revision": 1,
  "main_file_id": "11111111-1111-4111-8111-111111111111"
}
```

Успех HTTP 200 — `Settings`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `main_file_id` | `{"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Main File Id"}` | True |
| `engine` | `{"enum": ["pdflatex", "xelatex", "lualatex"], "title": "Engine", "type": "string"}` | True |
| `revision` | `{"minimum": 1, "title": "Revision", "type": "integer"}` | True |

Пример:
```json
{
  "engine": "pdflatex",
  "main_file_id": "11111111-1111-4111-8111-111111111111",
  "revision": 1
}
```

Ошибки: 400, 401, 403, 404, 409, 413, 415, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: projects, project_members, project_nodes; planned BE-046 audit будет добавлять event `update_settings`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-020` — правило use case; `API-020` — happy path и DTO;
`INT-API-020` — транзакция/rollback и конфликт; `SEC-API-020` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-022](../tasks/TASK-BE-022.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-045 — ListTemplates

`GET /api/v1/templates` · planned · operationId `list_templates` · tag `projects`.

Назначение и транзакция: Versioned seed manifest; без таблицы шаблонов.

Авторизация: `authenticated`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[]
```

Запрос — `none`:

Тело отсутствует.

Успех HTTP 200 — `Templates`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `items` | `{"items": {"$ref": "#/components/schemas/Template"}, "title": "Items", "type": "array"}` | True |

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

Таблицы: projects, project_members, project_nodes; planned BE-046 audit будет добавлять event `list_templates`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-045` — правило use case; `API-045` — happy path и DTO;
`INT-API-045` — транзакция/rollback и конфликт; `SEC-API-045` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-021](../tasks/TASK-BE-021.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-046 — ReadTemplate

`GET /api/v1/templates/{template_id}` · planned · operationId `read_template` · tag `projects`.

Назначение и транзакция: Только whitelist template_id из manifest; неизвестный 404.

Авторизация: `authenticated`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[
  {
    "in": "path",
    "name": "template_id",
    "required": true,
    "schema": {
      "maxLength": 80,
      "type": "string"
    }
  }
]
```

Запрос — `none`:

Тело отсутствует.

Успех HTTP 200 — `Template`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `id` | `{"title": "Id", "type": "string"}` | True |
| `title` | `{"title": "Title", "type": "string"}` | True |
| `description` | `{"title": "Description", "type": "string"}` | True |
| `engine` | `{"enum": ["pdflatex", "xelatex", "lualatex"], "title": "Engine", "type": "string"}` | True |
| `main_file` | `{"title": "Main File", "type": "string"}` | True |
| `files` | `{"items": {"type": "string"}, "title": "Files", "type": "array"}` | True |
| `version` | `{"title": "Version", "type": "string"}` | True |

Пример:
```json
{
  "description": "x",
  "engine": "pdflatex",
  "files": [],
  "id": "x",
  "main_file": "x",
  "title": "x",
  "version": "x"
}
```

Ошибки: 400, 401, 403, 404, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: projects, project_members, project_nodes; planned BE-046 audit будет добавлять event `read_template`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-046` — правило use case; `API-046` — happy path и DTO;
`INT-API-046` — транзакция/rollback и конфликт; `SEC-API-046` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-021](../tasks/TASK-BE-021.md),
[ADR-0001](../adr/0001-modular-monolith.md).
