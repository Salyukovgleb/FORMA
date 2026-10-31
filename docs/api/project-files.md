# API: project-files

Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30. Состояние реализации указано для каждого метода.

## API-021 — ReadTree

`GET /api/v1/projects/{project_id}/tree` · planned · operationId `read_tree` · tag `project-files`.

Назначение и транзакция: Один consistent SELECT; плоское дерево до 2000 live узлов и revision проекта.

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

Успех HTTP 200 — `Tree`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `project_revision` | `{"minimum": 1, "title": "Project Revision", "type": "integer"}` | True |
| `nodes` | `{"items": {"$ref": "#/components/schemas/Node"}, "title": "Nodes", "type": "array"}` | True |

Пример:
```json
{
  "nodes": [],
  "project_revision": 1
}
```

Ошибки: 400, 401, 403, 404, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: projects, project_nodes, file_revisions; mutation добавляет audit event `read_tree`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-021` — правило use case; `API-021` — happy path и DTO;
`INT-API-021` — транзакция/rollback и конфликт; `SEC-API-021` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-025](../tasks/TASK-BE-025.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-022 — CreateFolder

`POST /api/v1/projects/{project_id}/folders` · planned · operationId `create_folder` · tag `project-files`.

Назначение и транзакция: Lock project; проверить parent и имя; collision 409; увеличить project revision.

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

Запрос — `FolderCreate`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `parent_id` | `{"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "default": null, "title": "Parent Id"}` | False |
| `name` | `{"maxLength": 255, "minLength": 1, "title": "Name", "type": "string"}` | True |

Пример:
```json
{
  "name": "x",
  "parent_id": null
}
```

Успех HTTP 201 — `Node`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `id` | `{"format": "uuid", "title": "Id", "type": "string"}` | True |
| `project_id` | `{"format": "uuid", "title": "Project Id", "type": "string"}` | True |
| `parent_id` | `{"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Parent Id"}` | True |
| `name` | `{"title": "Name", "type": "string"}` | True |
| `node_type` | `{"enum": ["file", "folder"], "title": "Node Type", "type": "string"}` | True |
| `logical_path` | `{"title": "Logical Path", "type": "string"}` | True |
| `media_type` | `{"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Media Type"}` | True |
| `size_bytes` | `{"title": "Size Bytes", "type": "integer"}` | True |
| `content_hash` | `{"anyOf": [{"pattern": "^[0-9a-f]{64}$", "type": "string"}, {"type": "null"}], "title": "Content Hash"}` | True |
| `content_revision` | `{"anyOf": [{"minimum": 1, "type": "integer"}, {"type": "null"}], "title": "Content Revision"}` | True |
| `revision` | `{"minimum": 1, "title": "Revision", "type": "integer"}` | True |
| `created_at` | `{"format": "date-time", "title": "Created At", "type": "string"}` | True |
| `updated_at` | `{"format": "date-time", "title": "Updated At", "type": "string"}` | True |

Пример:
```json
{
  "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "content_revision": 1,
  "created_at": "2026-10-30T12:00:00Z",
  "id": "11111111-1111-4111-8111-111111111111",
  "logical_path": "x",
  "media_type": "x",
  "name": "x",
  "node_type": "file",
  "parent_id": "11111111-1111-4111-8111-111111111111",
  "project_id": "11111111-1111-4111-8111-111111111111",
  "revision": 1,
  "size_bytes": 1,
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

Таблицы: projects, project_nodes, file_revisions; mutation добавляет audit event `create_folder`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-022` — правило use case; `API-022` — happy path и DTO;
`INT-API-022` — транзакция/rollback и конфликт; `SEC-API-022` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-025](../tasks/TASK-BE-025.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-023 — CreateFile

`POST /api/v1/projects/{project_id}/files` · planned · operationId `create_file` · tag `project-files`.

Назначение и транзакция: Опубликовать immutable blob; lock project; INSERT node и revision 1; увеличить project revision.

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

Запрос — `FileCreate`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `parent_id` | `{"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "default": null, "title": "Parent Id"}` | False |
| `name` | `{"maxLength": 255, "minLength": 1, "title": "Name", "type": "string"}` | True |
| `content` | `{"default": "", "maxLength": 1048576, "title": "Content", "type": "string"}` | False |

Пример:
```json
{
  "content": "",
  "name": "x",
  "parent_id": null
}
```

Успех HTTP 201 — `Node`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `id` | `{"format": "uuid", "title": "Id", "type": "string"}` | True |
| `project_id` | `{"format": "uuid", "title": "Project Id", "type": "string"}` | True |
| `parent_id` | `{"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Parent Id"}` | True |
| `name` | `{"title": "Name", "type": "string"}` | True |
| `node_type` | `{"enum": ["file", "folder"], "title": "Node Type", "type": "string"}` | True |
| `logical_path` | `{"title": "Logical Path", "type": "string"}` | True |
| `media_type` | `{"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Media Type"}` | True |
| `size_bytes` | `{"title": "Size Bytes", "type": "integer"}` | True |
| `content_hash` | `{"anyOf": [{"pattern": "^[0-9a-f]{64}$", "type": "string"}, {"type": "null"}], "title": "Content Hash"}` | True |
| `content_revision` | `{"anyOf": [{"minimum": 1, "type": "integer"}, {"type": "null"}], "title": "Content Revision"}` | True |
| `revision` | `{"minimum": 1, "title": "Revision", "type": "integer"}` | True |
| `created_at` | `{"format": "date-time", "title": "Created At", "type": "string"}` | True |
| `updated_at` | `{"format": "date-time", "title": "Updated At", "type": "string"}` | True |

Пример:
```json
{
  "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "content_revision": 1,
  "created_at": "2026-10-30T12:00:00Z",
  "id": "11111111-1111-4111-8111-111111111111",
  "logical_path": "x",
  "media_type": "x",
  "name": "x",
  "node_type": "file",
  "parent_id": "11111111-1111-4111-8111-111111111111",
  "project_id": "11111111-1111-4111-8111-111111111111",
  "revision": 1,
  "size_bytes": 1,
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

Таблицы: projects, project_nodes, file_revisions; mutation добавляет audit event `create_file`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-023` — правило use case; `API-023` — happy path и DTO;
`INT-API-023` — транзакция/rollback и конфликт; `SEC-API-023` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-025](../tasks/TASK-BE-025.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-024 — UploadFile

`POST /api/v1/projects/{project_id}/uploads` · planned · operationId `upload_file` · tag `project-files`.

Назначение и транзакция: Потоковый staging до 20 MiB; whitelist MIME/extension; lock owner и project; quota; node/revision 1; без overwrite.

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

Запрос — `Upload`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `parent_id` | `{"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "default": null, "title": "Parent Id"}` | False |
| `file` | `{"format": "binary", "title": "File", "type": "string"}` | True |

Пример:
```json
{
  "file": "x",
  "parent_id": null
}
```

Успех HTTP 201 — `Node`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `id` | `{"format": "uuid", "title": "Id", "type": "string"}` | True |
| `project_id` | `{"format": "uuid", "title": "Project Id", "type": "string"}` | True |
| `parent_id` | `{"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Parent Id"}` | True |
| `name` | `{"title": "Name", "type": "string"}` | True |
| `node_type` | `{"enum": ["file", "folder"], "title": "Node Type", "type": "string"}` | True |
| `logical_path` | `{"title": "Logical Path", "type": "string"}` | True |
| `media_type` | `{"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Media Type"}` | True |
| `size_bytes` | `{"title": "Size Bytes", "type": "integer"}` | True |
| `content_hash` | `{"anyOf": [{"pattern": "^[0-9a-f]{64}$", "type": "string"}, {"type": "null"}], "title": "Content Hash"}` | True |
| `content_revision` | `{"anyOf": [{"minimum": 1, "type": "integer"}, {"type": "null"}], "title": "Content Revision"}` | True |
| `revision` | `{"minimum": 1, "title": "Revision", "type": "integer"}` | True |
| `created_at` | `{"format": "date-time", "title": "Created At", "type": "string"}` | True |
| `updated_at` | `{"format": "date-time", "title": "Updated At", "type": "string"}` | True |

Пример:
```json
{
  "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "content_revision": 1,
  "created_at": "2026-10-30T12:00:00Z",
  "id": "11111111-1111-4111-8111-111111111111",
  "logical_path": "x",
  "media_type": "x",
  "name": "x",
  "node_type": "file",
  "parent_id": "11111111-1111-4111-8111-111111111111",
  "project_id": "11111111-1111-4111-8111-111111111111",
  "revision": 1,
  "size_bytes": 1,
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

Таблицы: projects, project_nodes, file_revisions; mutation добавляет audit event `upload_file`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-024` — правило use case; `API-024` — happy path и DTO;
`INT-API-024` — транзакция/rollback и конфликт; `SEC-API-024` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-026](../tasks/TASK-BE-026.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-025 — ReadNode

`GET /api/v1/projects/{project_id}/nodes/{node_id}` · planned · operationId `read_node` · tag `project-files`.

Назначение и транзакция: Live node из указанного проекта; join текущей revision для размера/hash.

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
  },
  {
    "in": "path",
    "name": "node_id",
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

Успех HTTP 200 — `Node`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `id` | `{"format": "uuid", "title": "Id", "type": "string"}` | True |
| `project_id` | `{"format": "uuid", "title": "Project Id", "type": "string"}` | True |
| `parent_id` | `{"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Parent Id"}` | True |
| `name` | `{"title": "Name", "type": "string"}` | True |
| `node_type` | `{"enum": ["file", "folder"], "title": "Node Type", "type": "string"}` | True |
| `logical_path` | `{"title": "Logical Path", "type": "string"}` | True |
| `media_type` | `{"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Media Type"}` | True |
| `size_bytes` | `{"title": "Size Bytes", "type": "integer"}` | True |
| `content_hash` | `{"anyOf": [{"pattern": "^[0-9a-f]{64}$", "type": "string"}, {"type": "null"}], "title": "Content Hash"}` | True |
| `content_revision` | `{"anyOf": [{"minimum": 1, "type": "integer"}, {"type": "null"}], "title": "Content Revision"}` | True |
| `revision` | `{"minimum": 1, "title": "Revision", "type": "integer"}` | True |
| `created_at` | `{"format": "date-time", "title": "Created At", "type": "string"}` | True |
| `updated_at` | `{"format": "date-time", "title": "Updated At", "type": "string"}` | True |

Пример:
```json
{
  "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "content_revision": 1,
  "created_at": "2026-10-30T12:00:00Z",
  "id": "11111111-1111-4111-8111-111111111111",
  "logical_path": "x",
  "media_type": "x",
  "name": "x",
  "node_type": "file",
  "parent_id": "11111111-1111-4111-8111-111111111111",
  "project_id": "11111111-1111-4111-8111-111111111111",
  "revision": 1,
  "size_bytes": 1,
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

Таблицы: projects, project_nodes, file_revisions; mutation добавляет audit event `read_node`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-025` — правило use case; `API-025` — happy path и DTO;
`INT-API-025` — транзакция/rollback и конфликт; `SEC-API-025` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-025](../tasks/TASK-BE-025.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-026 — ReadContent

`GET /api/v1/projects/{project_id}/files/{file_id}/content` · planned · operationId `read_content` · tag `project-files`.

Назначение и транзакция: Только UTF-8 text до 1 MiB; binary даёт 415.

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
  },
  {
    "in": "path",
    "name": "file_id",
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

Успех HTTP 200 — `Content`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `file_id` | `{"format": "uuid", "title": "File Id", "type": "string"}` | True |
| `revision` | `{"minimum": 1, "title": "Revision", "type": "integer"}` | True |
| `content` | `{"title": "Content", "type": "string"}` | True |
| `content_hash` | `{"pattern": "^[0-9a-f]{64}$", "title": "Content Hash", "type": "string"}` | True |

Пример:
```json
{
  "content": "x",
  "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "file_id": "11111111-1111-4111-8111-111111111111",
  "revision": 1
}
```

Ошибки: 400, 401, 403, 404, 415, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: projects, project_nodes, file_revisions; mutation добавляет audit event `read_content`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-026` — правило use case; `API-026` — happy path и DTO;
`INT-API-026` — транзакция/rollback и конфликт; `SEC-API-026` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-027](../tasks/TASK-BE-027.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-027 — SaveFileContent

`PUT /api/v1/projects/{project_id}/files/{file_id}/content` · planned · operationId `save_file_content` · tag `project-files`.

Назначение и транзакция: Blob перед commit; lock owner/project/node; expected_revision; INSERT immutable revision N+1; увеличить project revision; stale 409.

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
  },
  {
    "in": "path",
    "name": "file_id",
    "required": true,
    "schema": {
      "format": "uuid",
      "type": "string"
    }
  }
]
```

Запрос — `SaveContent`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `content` | `{"maxLength": 1048576, "title": "Content", "type": "string"}` | True |
| `expected_revision` | `{"minimum": 1, "title": "Expected Revision", "type": "integer"}` | True |

Пример:
```json
{
  "content": "x",
  "expected_revision": 1
}
```

Успех HTTP 200 — `Content`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `file_id` | `{"format": "uuid", "title": "File Id", "type": "string"}` | True |
| `revision` | `{"minimum": 1, "title": "Revision", "type": "integer"}` | True |
| `content` | `{"title": "Content", "type": "string"}` | True |
| `content_hash` | `{"pattern": "^[0-9a-f]{64}$", "title": "Content Hash", "type": "string"}` | True |

Пример:
```json
{
  "content": "x",
  "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "file_id": "11111111-1111-4111-8111-111111111111",
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

Таблицы: projects, project_nodes, file_revisions; mutation добавляет audit event `save_file_content`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-027` — правило use case; `API-027` — happy path и DTO;
`INT-API-027` — транзакция/rollback и конфликт; `SEC-API-027` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-027](../tasks/TASK-BE-027.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-028 — MoveProjectNode

`PATCH /api/v1/projects/{project_id}/nodes/{node_id}` · planned · operationId `move_project_node` · tag `project-files`.

Назначение и транзакция: Lock project; expected_revision; запрет цикла/коллизии; обновить paths поддерева и node revisions; file revision не меняется.

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
  },
  {
    "in": "path",
    "name": "node_id",
    "required": true,
    "schema": {
      "format": "uuid",
      "type": "string"
    }
  }
]
```

Запрос — `NodePatch`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `name` | `{"maxLength": 255, "minLength": 1, "title": "Name", "type": "string"}` | True |
| `parent_id` | `{"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Parent Id"}` | True |
| `expected_revision` | `{"minimum": 1, "title": "Expected Revision", "type": "integer"}` | True |

Пример:
```json
{
  "expected_revision": 1,
  "name": "x",
  "parent_id": "11111111-1111-4111-8111-111111111111"
}
```

Успех HTTP 200 — `Node`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `id` | `{"format": "uuid", "title": "Id", "type": "string"}` | True |
| `project_id` | `{"format": "uuid", "title": "Project Id", "type": "string"}` | True |
| `parent_id` | `{"anyOf": [{"format": "uuid", "type": "string"}, {"type": "null"}], "title": "Parent Id"}` | True |
| `name` | `{"title": "Name", "type": "string"}` | True |
| `node_type` | `{"enum": ["file", "folder"], "title": "Node Type", "type": "string"}` | True |
| `logical_path` | `{"title": "Logical Path", "type": "string"}` | True |
| `media_type` | `{"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Media Type"}` | True |
| `size_bytes` | `{"title": "Size Bytes", "type": "integer"}` | True |
| `content_hash` | `{"anyOf": [{"pattern": "^[0-9a-f]{64}$", "type": "string"}, {"type": "null"}], "title": "Content Hash"}` | True |
| `content_revision` | `{"anyOf": [{"minimum": 1, "type": "integer"}, {"type": "null"}], "title": "Content Revision"}` | True |
| `revision` | `{"minimum": 1, "title": "Revision", "type": "integer"}` | True |
| `created_at` | `{"format": "date-time", "title": "Created At", "type": "string"}` | True |
| `updated_at` | `{"format": "date-time", "title": "Updated At", "type": "string"}` | True |

Пример:
```json
{
  "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "content_revision": 1,
  "created_at": "2026-10-30T12:00:00Z",
  "id": "11111111-1111-4111-8111-111111111111",
  "logical_path": "x",
  "media_type": "x",
  "name": "x",
  "node_type": "file",
  "parent_id": "11111111-1111-4111-8111-111111111111",
  "project_id": "11111111-1111-4111-8111-111111111111",
  "revision": 1,
  "size_bytes": 1,
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

Таблицы: projects, project_nodes, file_revisions; mutation добавляет audit event `move_project_node`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-028` — правило use case; `API-028` — happy path и DTO;
`INT-API-028` — транзакция/rollback и конфликт; `SEC-API-028` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-028](../tasks/TASK-BE-028.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-029 — DeleteNode

`DELETE /api/v1/projects/{project_id}/nodes/{node_id}` · planned · operationId `delete_node` · tag `project-files`.

Назначение и транзакция: Lock project; query expected_revision; recursive=false по умолчанию, непустая папка 409; main в поддереве 409; soft delete.

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
  },
  {
    "in": "path",
    "name": "node_id",
    "required": true,
    "schema": {
      "format": "uuid",
      "type": "string"
    }
  },
  {
    "in": "query",
    "name": "expected_revision",
    "required": true,
    "schema": {
      "minimum": 1,
      "type": "integer"
    }
  },
  {
    "in": "query",
    "name": "recursive",
    "schema": {
      "default": false,
      "type": "boolean"
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

Таблицы: projects, project_nodes, file_revisions; mutation добавляет audit event `delete_node`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-029` — правило use case; `API-029` — happy path и DTO;
`INT-API-029` — транзакция/rollback и конфликт; `SEC-API-029` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-028](../tasks/TASK-BE-028.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-030 — DownloadFile

`GET /api/v1/projects/{project_id}/files/{file_id}/download` · planned · operationId `download_file` · tag `project-files`.

Назначение и транзакция: Поток текущего immutable blob; только live file и действующий ACL.

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
  },
  {
    "in": "path",
    "name": "file_id",
    "required": true,
    "schema": {
      "format": "uuid",
      "type": "string"
    }
  },
  {
    "in": "query",
    "name": "disposition",
    "schema": {
      "default": "attachment",
      "enum": [
        "attachment",
        "inline"
      ],
      "type": "string"
    }
  }
]
```

Запрос — `none`:

Тело отсутствует.

Успех HTTP 200 — `Binary`:

Поток bytes; не JSON. MIME определяется сохранёнными метаданными и whitelist.

Ошибки: 400, 401, 403, 404, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: projects, project_nodes, file_revisions; mutation добавляет audit event `download_file`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-030` — правило use case; `API-030` — happy path и DTO;
`INT-API-030` — транзакция/rollback и конфликт; `SEC-API-030` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-026](../tasks/TASK-BE-026.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-031 — ListRevisions

`GET /api/v1/projects/{project_id}/files/{file_id}/revisions` · planned · operationId `list_revisions` · tag `project-files`.

Назначение и транзакция: Пагинация revision DESC; только live file.

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
  },
  {
    "in": "path",
    "name": "file_id",
    "required": true,
    "schema": {
      "format": "uuid",
      "type": "string"
    }
  },
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
  }
]
```

Запрос — `none`:

Тело отсутствует.

Успех HTTP 200 — `Page_FileRevision_`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `items` | `{"items": {"$ref": "#/components/schemas/FileRevision"}, "title": "Items", "type": "array"}` | True |
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

Таблицы: projects, project_nodes, file_revisions; mutation добавляет audit event `list_revisions`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-031` — правило use case; `API-031` — happy path и DTO;
`INT-API-031` — транзакция/rollback и конфликт; `SEC-API-031` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-029](../tasks/TASK-BE-029.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-032 — ReadRevision

`GET /api/v1/projects/{project_id}/files/{file_id}/revisions/{revision}` · planned · operationId `read_revision` · tag `project-files`.

Назначение и транзакция: Поток bytes выбранной retained revision; текст UTF-8; удалённая retention версия 404.

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
  },
  {
    "in": "path",
    "name": "file_id",
    "required": true,
    "schema": {
      "format": "uuid",
      "type": "string"
    }
  },
  {
    "in": "path",
    "name": "revision",
    "required": true,
    "schema": {
      "minimum": 1,
      "type": "integer"
    }
  },
  {
    "in": "query",
    "name": "disposition",
    "schema": {
      "default": "attachment",
      "enum": [
        "attachment",
        "inline"
      ],
      "type": "string"
    }
  }
]
```

Запрос — `none`:

Тело отсутствует.

Успех HTTP 200 — `Binary`:

Поток bytes; не JSON. MIME определяется сохранёнными метаданными и whitelist.

Ошибки: 400, 401, 403, 404, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: projects, project_nodes, file_revisions; mutation добавляет audit event `read_revision`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-032` — правило use case; `API-032` — happy path и DTO;
`INT-API-032` — транзакция/rollback и конфликт; `SEC-API-032` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-029](../tasks/TASK-BE-029.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-033 — RestoreFileRevision

`POST /api/v1/projects/{project_id}/files/{file_id}/revisions/{revision}/restore` · planned · operationId `restore_file_revision` · tag `project-files`.

Назначение и транзакция: Только text file; expected_revision относится к content revision; копия старого blob становится новой N+1; binary 415.

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
  },
  {
    "in": "path",
    "name": "file_id",
    "required": true,
    "schema": {
      "format": "uuid",
      "type": "string"
    }
  },
  {
    "in": "path",
    "name": "revision",
    "required": true,
    "schema": {
      "minimum": 1,
      "type": "integer"
    }
  }
]
```

Запрос — `RestoreRevision`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `expected_revision` | `{"minimum": 1, "title": "Expected Revision", "type": "integer"}` | True |

Пример:
```json
{
  "expected_revision": 1
}
```

Успех HTTP 200 — `Content`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `file_id` | `{"format": "uuid", "title": "File Id", "type": "string"}` | True |
| `revision` | `{"minimum": 1, "title": "Revision", "type": "integer"}` | True |
| `content` | `{"title": "Content", "type": "string"}` | True |
| `content_hash` | `{"pattern": "^[0-9a-f]{64}$", "title": "Content Hash", "type": "string"}` | True |

Пример:
```json
{
  "content": "x",
  "content_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "file_id": "11111111-1111-4111-8111-111111111111",
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

Таблицы: projects, project_nodes, file_revisions; mutation добавляет audit event `restore_file_revision`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-033` — правило use case; `API-033` — happy path и DTO;
`INT-API-033` — транзакция/rollback и конфликт; `SEC-API-033` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-029](../tasks/TASK-BE-029.md),
[ADR-0001](../adr/0001-modular-monolith.md).
