# API: documents

Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30. Состояние реализации указано для каждого метода.

## API-038 — RequestCompilation

`POST /api/v1/projects/{project_id}/compilations` · planned · operationId `request_compilation` · tag `documents`.

Назначение и транзакция: Lock owner/project; ACL; idempotency; expected_project_revision; INSERT snapshot/entries/job атомарно; main обязателен.

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
    "in": "header",
    "name": "Idempotency-Key",
    "required": true,
    "schema": {
      "maxLength": 128,
      "minLength": 16,
      "type": "string"
    }
  }
]
```

Запрос — `Compile`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `expected_project_revision` | `{"minimum": 1, "title": "Expected Project Revision", "type": "integer"}` | True |

Пример:
```json
{
  "expected_project_revision": 1
}
```

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

Ошибки: 400, 401, 403, 404, 409, 413, 415, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: projects, project_snapshots, snapshot_entries, document_jobs; planned BE-046 audit будет добавлять event `request_compilation`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-038` — правило use case; `API-038` — happy path и DTO;
`INT-API-038` — транзакция/rollback и конфликт; `SEC-API-038` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-037](../tasks/TASK-BE-037.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-039 — RequestExport

`POST /api/v1/projects/{project_id}/exports` · planned · operationId `request_export` · tag `documents`.

Назначение и транзакция: Lock owner/project; ACL; idempotency; snapshot/entries/job атомарно; docx требует main, zip допускает пустое дерево.

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
    "in": "header",
    "name": "Idempotency-Key",
    "required": true,
    "schema": {
      "maxLength": 128,
      "minLength": 16,
      "type": "string"
    }
  }
]
```

Запрос — `Export`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `expected_project_revision` | `{"minimum": 1, "title": "Expected Project Revision", "type": "integer"}` | True |
| `format` | `{"enum": ["docx", "zip"], "title": "Format", "type": "string"}` | True |
| `reference_id` | `{"const": "forma-default-v1", "default": "forma-default-v1", "title": "Reference Id", "type": "string"}` | False |

Пример:
```json
{
  "expected_project_revision": 1,
  "format": "docx",
  "reference_id": "forma-default-v1"
}
```

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

Ошибки: 400, 401, 403, 404, 409, 413, 415, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: projects, project_snapshots, snapshot_entries, document_jobs; planned BE-046 audit будет добавлять event `request_export`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-039` — правило use case; `API-039` — happy path и DTO;
`INT-API-039` — транзакция/rollback и конфликт; `SEC-API-039` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-044](../tasks/TASK-BE-044.md),
[ADR-0001](../adr/0001-modular-monolith.md).
