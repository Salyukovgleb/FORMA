# Ошибки

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

Envelope строго `{error:{code,message,details,request_id}}`; details — typed object
field/current_revision/retry_after/reason (nullable). Текст message не API для ветвления.

| HTTP | code | Смысл |
|---|---|---|
| 400 | INVALID_CURSOR, INVALID_REQUEST | Не удалось декодировать transport/cursor |
| 401 | UNAUTHENTICATED, SESSION_EXPIRED, TOKEN_REPLAY | Нет действующей сессии |
| 403 | FORBIDDEN, CSRF_FAILED | Видимый объект, недостаточные права / CSRF |
| 404 | NOT_FOUND, USER_NOT_FOUND | Скрытый/отсутствующий объект, unknown invite target |
| 409 | REVISION_CONFLICT, NAME_CONFLICT, EMAIL_TAKEN, IDEMPOTENCY_CONFLICT | Конкурентность/уникальность |
| 409 | INVALID_STATE, OWNER_IMMUTABLE, MAIN_FILE_IN_USE | Доменный запрет |
| 410 | RETENTION_EXPIRED, ARTIFACT_EXPIRED | Owner restore после срока / expired download |
| 413 | PAYLOAD_TOO_LARGE | Bytes limit |
| 415 | UNSUPPORTED_MEDIA_TYPE | Format/MIME/text-only operation |
| 422 | VALIDATION_ERROR, INVALID_PATH, INVALID_MAIN_FILE | Схема/семантика input |
| 429 | RATE_LIMITED, QUOTA_EXCEEDED | Retry-After seconds (quota: retention/manual cleanup) |
| 500 | INTERNAL_ERROR | Только generic message, traceback в защищённом log |
| 405 | METHOD_NOT_ALLOWED | Неподдерживаемый HTTP метод, заголовок Allow сохраняется |
| 503 | STORAGE_UNAVAILABLE, DATABASE_UNAVAILABLE, DEPENDENCY_UNAVAILABLE | Dependency недоступна |

Job error_code отдельно: LATEX_COMPILATION_FAILED, DOCX_CONVERSION_FAILED,
INVALID_SNAPSHOT, TIMEOUT, RESOURCE_LIMIT, WORKER_LOST, TEMPORARY_IO,
DATABASE_UNAVAILABLE, CANCELLED. HTTP 202 не означает успешный результат job.
FastAPI validation exception переводится в envelope, стандартный detail[] не выдаётся.
При нескольких validation errors вернуть первую детерминированно и request_id.

BE-012: error envelope реализован на HTTP boundary; значения input, HTTPException.detail и exception text не сериализуются. details.field может быть null; runtime не отражает произвольные ключи запроса.
