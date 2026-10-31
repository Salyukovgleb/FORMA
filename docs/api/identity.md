# API: identity

Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30. Состояние реализации указано для каждого метода.

## API-003 — RegisterUser

`POST /api/v1/auth/register` · implemented · operationId `register_user` · tag `identity`.

Назначение и транзакция: Нормализовать email; hash пароля; INSERT user; дубликат 409 EMAIL_TAKEN. Сессия не создаётся.

Авторизация: `public`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[]
```

Запрос — `Register`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `email` | `{"maxLength": 254, "minLength": 3, "pattern": "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$", "title": "Email", "type": "string"}` | True |
| `password` | `{"maxLength": 128, "minLength": 12, "title": "Password", "type": "string"}` | True |
| `display_name` | `{"maxLength": 100, "minLength": 1, "title": "Display Name", "type": "string"}` | True |

Пример:
```json
{
  "display_name": "x",
  "email": "user@example.org",
  "password": "xxxxxxxxxxxx"
}
```

Успех HTTP 201 — `Profile`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `id` | `{"format": "uuid", "title": "Id", "type": "string"}` | True |
| `email` | `{"maxLength": 254, "minLength": 3, "pattern": "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$", "title": "Email", "type": "string"}` | True |
| `display_name` | `{"title": "Display Name", "type": "string"}` | True |
| `created_at` | `{"format": "date-time", "title": "Created At", "type": "string"}` | True |

Пример:
```json
{
  "created_at": "2026-10-30T12:00:00Z",
  "display_name": "x",
  "email": "user@example.org",
  "id": "11111111-1111-4111-8111-111111111111"
}
```

Ошибки: 400, 409, 413, 415, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: users, auth_sessions, used_refresh_tokens, rate_limit_buckets; planned BE-046 audit будет добавлять event `register_user`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-003` — правило use case; `API-003` — happy path и DTO;
`INT-API-003` — транзакция/rollback и конфликт; `SEC-API-003` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-014](../tasks/TASK-BE-014.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-004 — Login

`POST /api/v1/auth/login` · planned · operationId `login` · tag `identity`.

Назначение и транзакция: Проверить пароль; INSERT session; установить refresh cookie и вернуть access/CSRF.

Авторизация: `public`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[]
```

Запрос — `Login`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `email` | `{"maxLength": 254, "minLength": 3, "pattern": "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$", "title": "Email", "type": "string"}` | True |
| `password` | `{"maxLength": 128, "minLength": 1, "title": "Password", "type": "string"}` | True |

Пример:
```json
{
  "email": "user@example.org",
  "password": "x"
}
```

Успех HTTP 200 — `Token`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `access_token` | `{"title": "Access Token", "type": "string"}` | True |
| `token_type` | `{"const": "bearer", "default": "bearer", "title": "Token Type", "type": "string"}` | False |
| `expires_in` | `{"const": 600, "default": 600, "title": "Expires In", "type": "integer"}` | False |
| `csrf_token` | `{"title": "Csrf Token", "type": "string"}` | True |

Пример:
```json
{
  "access_token": "x",
  "csrf_token": "x",
  "expires_in": 600,
  "token_type": "bearer"
}
```

Ошибки: 400, 409, 413, 415, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: users, auth_sessions, used_refresh_tokens, rate_limit_buckets; planned BE-046 audit будет добавлять event `login`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-004` — правило use case; `API-004` — happy path и DTO;
`INT-API-004` — транзакция/rollback и конфликт; `SEC-API-004` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-015](../tasks/TASK-BE-015.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-005 — RotateSession

`POST /api/v1/auth/refresh` · planned · operationId `rotate_session` · tag `identity`.

Назначение и транзакция: Lock session; использованный hash в used_refresh_tokens; заменить refresh/CSRF hashes. Replay отзывает session.

Авторизация: `refresh`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[
  {
    "in": "header",
    "name": "X-CSRF-Token",
    "required": true,
    "schema": {
      "maxLength": 128,
      "minLength": 32,
      "type": "string"
    }
  }
]
```

Запрос — `none`:

Тело отсутствует.

Успех HTTP 200 — `Token`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `access_token` | `{"title": "Access Token", "type": "string"}` | True |
| `token_type` | `{"const": "bearer", "default": "bearer", "title": "Token Type", "type": "string"}` | False |
| `expires_in` | `{"const": 600, "default": 600, "title": "Expires In", "type": "integer"}` | False |
| `csrf_token` | `{"title": "Csrf Token", "type": "string"}` | True |

Пример:
```json
{
  "access_token": "x",
  "csrf_token": "x",
  "expires_in": 600,
  "token_type": "bearer"
}
```

Ошибки: 400, 401, 403, 404, 409, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: users, auth_sessions, used_refresh_tokens, rate_limit_buckets; planned BE-046 audit будет добавлять event `rotate_session`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-005` — правило use case; `API-005` — happy path и DTO;
`INT-API-005` — транзакция/rollback и конфликт; `SEC-API-005` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-015](../tasks/TASK-BE-015.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-006 — Logout

`POST /api/v1/auth/logout` · planned · operationId `logout` · tag `identity`.

Назначение и транзакция: Отозвать текущую session и очистить cookie; повторный отзыв 204, невалидный token 401.

Авторизация: `refresh`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[
  {
    "in": "header",
    "name": "X-CSRF-Token",
    "required": true,
    "schema": {
      "maxLength": 128,
      "minLength": 32,
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

Таблицы: users, auth_sessions, used_refresh_tokens, rate_limit_buckets; planned BE-046 audit будет добавлять event `logout`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-006` — правило use case; `API-006` — happy path и DTO;
`INT-API-006` — транзакция/rollback и конфликт; `SEC-API-006` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-015](../tasks/TASK-BE-015.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-007 — LogoutAll

`POST /api/v1/auth/logout-all` · planned · operationId `logout_all` · tag `identity`.

Назначение и транзакция: Отозвать все session пользователя; очистить cookie.

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

Успех HTTP 204 — `none`:

Тело отсутствует.

Ошибки: 400, 401, 403, 404, 409, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: users, auth_sessions, used_refresh_tokens, rate_limit_buckets; planned BE-046 audit будет добавлять event `logout_all`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-007` — правило use case; `API-007` — happy path и DTO;
`INT-API-007` — транзакция/rollback и конфликт; `SEC-API-007` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-015](../tasks/TASK-BE-015.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-008 — ReadProfile

`GET /api/v1/users/me` · planned · operationId `read_profile` · tag `identity`.

Назначение и транзакция: SELECT текущего пользователя.

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

Успех HTTP 200 — `Profile`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `id` | `{"format": "uuid", "title": "Id", "type": "string"}` | True |
| `email` | `{"maxLength": 254, "minLength": 3, "pattern": "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$", "title": "Email", "type": "string"}` | True |
| `display_name` | `{"title": "Display Name", "type": "string"}` | True |
| `created_at` | `{"format": "date-time", "title": "Created At", "type": "string"}` | True |

Пример:
```json
{
  "created_at": "2026-10-30T12:00:00Z",
  "display_name": "x",
  "email": "user@example.org",
  "id": "11111111-1111-4111-8111-111111111111"
}
```

Ошибки: 400, 401, 403, 404, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: users, auth_sessions, used_refresh_tokens, rate_limit_buckets; planned BE-046 audit будет добавлять event `read_profile`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-008` — правило use case; `API-008` — happy path и DTO;
`INT-API-008` — транзакция/rollback и конфликт; `SEC-API-008` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-016](../tasks/TASK-BE-016.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-009 — UpdateProfile

`PATCH /api/v1/users/me` · planned · operationId `update_profile` · tag `identity`.

Назначение и транзакция: Lock user; изменить display_name. Email неизменяем в MVP.

Авторизация: `authenticated`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[]
```

Запрос — `ProfilePatch`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `display_name` | `{"maxLength": 100, "minLength": 1, "title": "Display Name", "type": "string"}` | True |

Пример:
```json
{
  "display_name": "x"
}
```

Успех HTTP 200 — `Profile`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `id` | `{"format": "uuid", "title": "Id", "type": "string"}` | True |
| `email` | `{"maxLength": 254, "minLength": 3, "pattern": "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$", "title": "Email", "type": "string"}` | True |
| `display_name` | `{"title": "Display Name", "type": "string"}` | True |
| `created_at` | `{"format": "date-time", "title": "Created At", "type": "string"}` | True |

Пример:
```json
{
  "created_at": "2026-10-30T12:00:00Z",
  "display_name": "x",
  "email": "user@example.org",
  "id": "11111111-1111-4111-8111-111111111111"
}
```

Ошибки: 400, 401, 403, 404, 409, 413, 415, 422, 429, 500, 503; единая [модель](../15_ERROR_MODEL.md).
Чужой project/object → 404; доступный объект с запрещённой операцией → 403;
невалидный input → 422; конфликт revision/name/state → 409.

Идемпотентность: GET без изменений. Повторы mutation только после чтения актуального состояния;
компиляция/export используют Idempotency-Key; тот же ключ с другим телом → 409.
`expected_revision` сравнивается под блокировкой; не заменять If-Match.
Особые повторные вызовы и эффекты указаны в назначении метода выше.

Таблицы: users, auth_sessions, used_refresh_tokens, rate_limit_buckets; planned BE-046 audit будет добавлять event `update_profile`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-009` — правило use case; `API-009` — happy path и DTO;
`INT-API-009` — транзакция/rollback и конфликт; `SEC-API-009` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-016](../tasks/TASK-BE-016.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-010 — ChangePassword

`POST /api/v1/users/me/change-password` · planned · operationId `change_password` · tag `identity`.

Назначение и транзакция: Проверить current_password; lock user; обновить hash; отозвать все сессии включая текущую.

Авторизация: `authenticated`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[]
```

Запрос — `PasswordChange`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `current_password` | `{"title": "Current Password", "type": "string"}` | True |
| `new_password` | `{"maxLength": 128, "minLength": 12, "title": "New Password", "type": "string"}` | True |

Пример:
```json
{
  "current_password": "x",
  "new_password": "xxxxxxxxxxxx"
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

Таблицы: users, auth_sessions, used_refresh_tokens, rate_limit_buckets; planned BE-046 audit будет добавлять event `change_password`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-010` — правило use case; `API-010` — happy path и DTO;
`INT-API-010` — транзакция/rollback и конфликт; `SEC-API-010` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-016](../tasks/TASK-BE-016.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-011 — ListSessions

`GET /api/v1/auth/sessions` · planned · operationId `list_sessions` · tag `identity`.

Назначение и транзакция: Только собственные неотозванные сессии.

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
  }
]
```

Запрос — `none`:

Тело отсутствует.

Успех HTTP 200 — `Page_Session_`:

| Поле | JSON schema | Обязательное |
|---|---|---|
| `items` | `{"items": {"$ref": "#/components/schemas/Session"}, "title": "Items", "type": "array"}` | True |
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

Таблицы: users, auth_sessions, used_refresh_tokens, rate_limit_buckets; planned BE-046 audit будет добавлять event `list_sessions`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-011` — правило use case; `API-011` — happy path и DTO;
`INT-API-011` — транзакция/rollback и конфликт; `SEC-API-011` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-015](../tasks/TASK-BE-015.md),
[ADR-0001](../adr/0001-modular-monolith.md).

## API-012 — RevokeSession

`DELETE /api/v1/auth/sessions/{session_id}` · planned · operationId `revoke_session` · tag `identity`.

Назначение и транзакция: Lock session своего пользователя; чужая/отсутствующая 404; повторный отзыв 204.

Авторизация: `authenticated`; точная матрица в [auth](../10_AUTH_AND_AUTHORIZATION.md).
Заголовки: Bearer для authenticated/ролей; refresh cookie + X-CSRF-Token для refresh;
Content-Type JSON кроме multipart upload; ответы X-Request-ID, Cache-Control: no-store.
Login/refresh устанавливают HttpOnly refresh cookie. Для cookie-запросов проверяется Origin.

Параметры (required/default/type определены явно):
```json
[
  {
    "in": "path",
    "name": "session_id",
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

Таблицы: users, auth_sessions, used_refresh_tokens, rate_limit_buckets; planned BE-046 audit будет добавлять event `revoke_session`
(кроме health и чтения); session/password/token никогда не попадают в metadata.
Storage: файловые операции — immutable revision blobs, jobs — pinned snapshots/artifacts;
прочие методы не пишут пользовательские blobs.
Лимиты: [NFR](../23_NON_FUNCTIONAL_REQUIREMENTS.md); body ограничивается до разбора JSON,
поток upload ограничивается во время чтения, ACL проверяется до скачивания.

Тесты planned: `UNIT-API-012` — правило use case; `API-012` — happy path и DTO;
`INT-API-012` — транзакция/rollback и конфликт; `SEC-API-012` — чужой пользователь/роль,
подмена path ID, отсутствие credentials, превышение лимита. Проверить каждый объявленный error.
Связи: [BE-015](../tasks/TASK-BE-015.md),
[ADR-0001](../adr/0001-modular-monolith.md).
