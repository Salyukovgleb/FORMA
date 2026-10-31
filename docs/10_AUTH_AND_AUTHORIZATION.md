# Auth и ACL

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

Access JWT HS256 TTL 10 минут, claims sub/sid/iss/aud/iat/exp/jti. Secret ≥32 random bytes,
rotation через kid и набор активных ключей. JWT algorithm allowlist строго HS256.
Каждый запрос проверяет active user и неотозванную, неистёкшую session в БД: revoke немедленный.
Refresh — random 256-bit opaque token; SHA-256 в auth_sessions, абсолютный TTL 30 суток.
Пароль — stdlib hashlib.scrypt N=32768,r=8,p=1, salt 16 random bytes, dklen=64;
хранить version+params+salt+hash, compare_digest, ограничить parallel hash attempts.
Это не дополнительный auth server. JWT библиотека PyJWT и psycopg обоснованы ADR-0006.

Transport: access только в памяти frontend, Authorization Bearer; refresh cookie
HttpOnly, Secure, SameSite=Strict, Path=/api/v1/auth. Frontend/API same-site production.
Login выдаёт CSRF token в JSON, session хранит hash. Refresh/logout требуют X-CSRF-Token
и exact Origin allowlist. CORS только explicit origins, credentials=true, wildcard запрещён.
После перезагрузки страницы access/CSRF отсутствуют: пользователь входит снова; silent refresh
между перезагрузками вне MVP, это явное ограничение. Между вкладками refresh координируется
frontend, иначе replay отзывает session. Dev HTTP localhost разрешает insecure cookie только
при APP_ENV=development, production startup запрещает этот флаг.

Rotation: lock session; старый hash сохранить в used_refresh_tokens до absolute expiry;
записать новый refresh/CSRF hash, commit, Set-Cookie. Replay любого старого hash отзывает session.
Потерянный HTTP ответ rotation требует повторного login; grace window не вводится.
Password change отзывает все session. Email normalize strip/lower, без Gmail-dot aliases.

| ACL code | owner | editor | viewer | Дополнительное условие |
|---|---|---|---|---|
| reader | да | да | да | active проект |
| writer | да | да | нет | compile и изменения |
| owner | да | нет | нет | delete/restore/roles |
| owner_or_self | да | self | self | owner не может выйти |
| owner_or_requester | да | requester | requester | requester остаётся участником |
| authenticated | свой account | свой account | свой account | valid session |
| refresh | — | — | — | valid cookie+CSRF+Origin |
| public | — | — | — | health/register/login, Origin для login |

Видимость deleted: только owner read/restore; остальные endpoints возвращают 404.
Чужой объект и отсутствующий объект одинаково 404, запрещённое действие видимого объекта 403.
Все child IDs сверяются с project_id; знание UUID не даёт доступа. До выполнения queued job
worker проверяет active project, requester membership и право для job_type; потеря доступа
отменяет job. Running результат не выдаётся без текущего ACL; удаление проекта отменяет jobs.

## BE-014 implemented

POST /api/v1/auth/register создаёт user с normalized strip/lower email и scrypt hash.
maxmem=64MiB учитывает OpenSSL overhead; принимается только фиксированный v1 hash format.
Конкурентные hash operations≤2; неверные stored parameters не исполняются.
Rate bucket10/15min по HMAC socket peer; Retry-After900. Cleanup/остальные auth limits — BE-018.
API не выдаёт сессию при регистрации. Password repr скрыт; request JSON нужен только на входе.
Durable audit — BE-046. Login/refresh/revoke остаются BE-015, не считать их implemented.

## BE-015 implemented

Login, refresh, logout/logout-all, session list/revoke реализованы. JWT key ID задаётся
JWT_KEY_ID (v1 default); для graceful rotation задать вместе JWT_PREVIOUS_KEY_ID и
JWT_PREVIOUS_SECRET. Пустая пара выключает previous key. Удалить previous key после10min;
при компрометации drop немедленно и revoke sessions согласно incident procedure.
Секреты только в окружении; Compose передаёт key fields явно. PyJWT2.15.1, fixed HS256;
никаких remote JWK lookups. Origin обязателен для login/refresh/logout, CSRF32..128 для
refresh/logout; отсутствие required header →422, неверное значение →403. Account reload
по-прежнему требует login (ADR-0006). Login10/15min IP+email, refresh30/min session.
Current access сверяется с DB на каждом protected request; JSON/HTTP errors не содержат
токены. Logout повторно с тем же cookie+CSRF до expiry →204; без cookie →401.
User session pagination cursor v1 содержит created_at/id/filter; foreign UUID →404.
rotated_at меняется только при замене refresh hash, revoked_at сохраняет первый отзыв.

## BE-016 implemented

Профиль доступен только текущему authenticated user. PATCH принимает только display_name1..100;
extra fields/email/id →422. Password change: current1..128, new12..128, Unicode/NUL validation;
неверный current →401 без изменений. Лимит10/15min по HMAC user ID, 429 Retry-After900.
Под user lock повторно проверяется session, проверяется latest hash, затем password_hash/updated_at
и revoke-all обновляются в одной transaction. Ошибка до commit откатывает оба эффекта.
Login использует тот же lock; конкурентный login со старым паролем не создаёт сессию после change.
204 очищает cookie, все старые access/refresh отклоняются. Нужен новый login.
JSON body cap2MiB до parse применяется к PATCH/profile и POST/password, secret repr скрыт.
