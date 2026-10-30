# API: jobs

Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30. Реализация: planned.

## API-040 — ListJobs

`GET /api/v1/projects/{project_id}/jobs` · planned · operationId `list_jobs` · tag `jobs`.

Назначение и транзакция: Jobs проекта по queued_at DESC,id DESC; не возвращать внутренние ключи.

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

Успех HTTP 200 — `Page_Job_`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `items` | `{"items": {"$ref": "#/components/schemas/Job"}, "title": "Items", "type": "array"}` | True |
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

Таблицы: document_jobs, job_artifacts, job_log_entries, projects; mutation добавляет audit event `list_jobs`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-040` — правило use case; `API-040` — happy path и DTO;
`INT-API-040` — транзакция/rollback и конфликт; `SEC-API-040` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-037](../tasks/TASK-BE-037.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-041 — ReadJob

`GET /api/v1/projects/{project_id}/jobs/{job_id}` · planned · operationId `read_job` · tag `jobs`.

Назначение и транзакция: SELECT job + artifacts; ошибки и warnings читаются через logs.

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
    "name": "job_id",
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

Успех HTTP 200 — `Job`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `id` | `{"format": "uuid", "title": "Id", "type": "string"}` | True |
| `project_id` | `{"format": "uuid", "title": "Project Id", "type": "string"}` | True |
| `requested_by` | `{"format": "uuid", "title": "Requested By", "type": "string"}` | True |
| `job_type` | `{"enum": ["pdf", "docx", "zip"], "title": "Job Type", "type": "string"}` | True |
| `state` | `{"enum": ["queued", "running", "retry_wait", "succeeded", "failed", "cancelled"], "title": "State", "type": "string"}` | True |
| `stage` | `{"enum": ["waiting", "snapshot", "processing", "publishing", "complete"], "title": "Stage", "type": "string"}` | True |
| `attempt` | `{"title": "Attempt", "type": "integer"}` | True |
| `project_revision` | `{"minimum": 1, "title": "Project Revision", "type": "integer"}` | True |
| `queued_at` | `{"format": "date-time", "title": "Queued At", "type": "string"}` | True |
| `started_at` | `{"anyOf": [{"format": "date-time", "type": "string"}, {"type": "null"}], "title": "Started At"}` | True |
| `finished_at` | `{"anyOf": [{"format": "date-time", "type": "string"}, {"type": "null"}], "title": "Finished At"}` | True |
| `cancellation_requested` | `{"title": "Cancellation Requested", "type": "boolean"}` | True |
| `error_code` | `{"anyOf": [{"type": "string"}, {"type": "null"}], "title": "Error Code"}` | True |
| `artifacts` | `{"items": {"$ref": "#/components/schemas/Artifact"}, "title": "Artifacts", "type": "array"}` | True |
| `warnings` | `{"items": {"$ref": "#/components/schemas/JobLog"}, "maxItems": 100, "title": "Warnings", "type": "array"}` | True |

Пример:
```json
{
  "artifacts": [],
  "attempt": 1,
  "cancellation_requested": false,
  "error_code": "x",
  "finished_at": "2026-10-30T12:00:00Z",
  "id": "11111111-1111-4111-8111-111111111111",
  "job_type": "pdf",
  "project_id": "11111111-1111-4111-8111-111111111111",
  "project_revision": 1,
  "queued_at": "2026-10-30T12:00:00Z",
  "requested_by": "11111111-1111-4111-8111-111111111111",
  "stage": "waiting",
  "started_at": "2026-10-30T12:00:00Z",
  "state": "queued",
  "warnings": []
}
```

Ошибки: 400, 401, 403, 404, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: document_jobs, job_artifacts, job_log_entries, projects; mutation добавляет audit event `read_job`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-041` — правило use case; `API-041` — happy path и DTO;
`INT-API-041` — транзакция/rollback и конфликт; `SEC-API-041` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-037](../tasks/TASK-BE-037.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-042 — ReadJobLogs

`GET /api/v1/projects/{project_id}/jobs/{job_id}/logs` · planned · operationId `read_job_logs` · tag `jobs`.

Назначение и транзакция: Keyset sequence ASC; максимум 100 строк за ответ; paths только из snapshot.

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
    "name": "job_id",
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

Успех HTTP 200 — `Page_JobLog_`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `items` | `{"items": {"$ref": "#/components/schemas/JobLog"}, "title": "Items", "type": "array"}` | True |
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

Таблицы: document_jobs, job_artifacts, job_log_entries, projects; mutation добавляет audit event `read_job_logs`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-042` — правило use case; `API-042` — happy path и DTO;
`INT-API-042` — транзакция/rollback и конфликт; `SEC-API-042` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-037](../tasks/TASK-BE-037.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-043 — CancelJob

`POST /api/v1/projects/{project_id}/jobs/{job_id}/cancel` · planned · operationId `cancel_job` · tag `jobs`.

Назначение и транзакция: Текущий участник-requester или owner; lock job; queued/retry_wait → cancelled, running выставляет cancellation_requested; terminal возвращается без изменения.

Авторизация: `owner_or_requester`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
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
    "name": "job_id",
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

Успех HTTP 202 — `JobAccepted`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `job_id` | `{"format": "uuid", "title": "Job Id", "type": "string"}` | True |
| `state` | `{"enum": ["queued", "running", "retry_wait", "succeeded", "failed", "cancelled"], "title": "State", "type": "string"}` | True |
| `project_revision` | `{"minimum": 1, "title": "Project Revision", "type": "integer"}` | True |

Пример:
```json
{
  "job_id": "11111111-1111-4111-8111-111111111111",
  "project_revision": 1,
  "state": "queued"
}
```

Ошибки: 400, 401, 403, 404, 409, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: document_jobs, job_artifacts, job_log_entries, projects; mutation добавляет audit event `cancel_job`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-043` — правило use case; `API-043` — happy path и DTO;
`INT-API-043` — транзакция/rollback и конфликт; `SEC-API-043` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-037](../tasks/TASK-BE-037.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-044 — DownloadArtifact

`GET /api/v1/projects/{project_id}/artifacts/{artifact_id}/download` · planned · operationId `download_artifact` · tag `jobs`.

Назначение и транзакция: Join artifact/job/project; expiry 410; поток immutable bytes; ACL проверяется при каждом запросе.

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
    "name": "artifact_id",
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

Ошибки: 400, 401, 403, 404, 410, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: document_jobs, job_artifacts, job_log_entries, projects; mutation добавляет audit event `download_artifact`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-044` — правило use case; `API-044` — happy path и DTO;
`INT-API-044` — транзакция/rollback и конфликт; `SEC-API-044` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-037](../tasks/TASK-BE-037.md),
[ADR-0001](../adr/0001-modular-monolith.md).
