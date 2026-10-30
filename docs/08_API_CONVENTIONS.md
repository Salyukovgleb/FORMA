# Соглашения API

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

API /api/v1; health /health/live и /health/ready. [OpenAPI](contracts/openapi.json)
генерируется из Pydantic v2 и [registry](contracts/registry.py); все методы planned.
Runtime /openapi.json и /docs появятся в BE-012, должны совпасть с контрактом после реализации.
JSON extra fields запрещены. UUID canonical, даты RFC3339 UTC, UTF-8. PATCH здесь заменяет
явно перечисленный набор полей; отсутствующие обязательные поля дают 422.

Pagination: limit default 50, range 1..100; next_cursor nullable opaque base64url JSON
с version=1, last sort key и hash фильтра. Cursor не является ACL; фильтр сверяется и
доступ проверяется заново. Некорректный cursor 400 INVALID_CURSOR. Projects/sessions по
created_at DESC,id DESC; jobs queued_at DESC,id DESC; revisions revision DESC;
logs sequence ASC. Между страницами не гарантируется snapshot isolation; дублей при
неизменных ключах быть не должно. q до 200 символов, escaped substring title ILIKE;
status=deleted только owner. Tree bounded 2000 узлов и возвращается целиком.

Content PUT/restore принимают expected_revision содержимого; rename/delete — metadata revision;
project/settings — project revision. Stale →409 REVISION_CONFLICT с current_revision.
Компиляция/export требуют Idempotency-Key 16..128 ASCII и expected_project_revision.
Ключ уникален project/requester; hash включает route, нормализованное тело; повтор возвращает
тот же job_id даже terminal, иной hash 409 IDEMPOTENCY_CONFLICT. ACL проверяется до replay.
Ключ хранится 30 суток вместе с job; после удаления job повтор может создать новое задание.

Upload multipart file + optional parent_id; filename берётся из part, валидируется как basename.
20 MiB bytes; JSON body 2 MiB, текст после UTF-8 encoding ≤1 MiB. Default MIME по allowlist.
Download потоковый, no-store, nosniff, Content-Disposition RFC5987 filename* и ASCII fallback;
inline разрешён только PDF, остальное attachment. Range в MVP не поддерживается, полный 200.
При ошибке после начала потока соединение закрывается; JSON envelope уже отправлять нельзя.
