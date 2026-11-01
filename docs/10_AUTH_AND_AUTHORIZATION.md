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

## BE-017: implemented policy, repository integration pending

`modules/access/policy.py` — чистая stateless policy, принимает проверенный Principal и
immutable ProjectAccessContext из trusted repository текущего UoW. Она не выполняет
authentication, SQL, commit и не кэширует grants. Owner вычисляется из owner_id;
ProjectMembership принимает только MemberRole.EDITOR/VIEWER, с project_id и user_id.
Чужая membership не даёт прав. Role из JSON/JWT не является входом policy.

| Вызов | Scope / правило |
|---|---|
| require_project_permission | reader/writer/owner/restore; возвращает вычисленный ProjectRole |
| require_object_permission | дополнительно сверяет object_id и project_id с route до проверки прав; owner_or_requester берёт requester из object context |
| require_member_change | grant/change owner-only; remove owner_or_self; owner target →409 OWNER_IMMUTABLE после проверки прав |

Нет проекта/членства, несовпадение project/object/user IDs →404 NOT_FOUND; видимый
active project без нужных прав →403 FORBIDDEN. Conditional permissions нельзя вызвать
без member/object scope. Unknown permission fail-closed. Requester должен оставаться
участником; owner вправе отменять job другого requester. Deleted project доступен только
owner для project read/restore; child/member/прочие operations →404, включая owner.
Restore active project разрешается policy для owner, state/retention проверяет use case.

Contexts не строятся из transport. Mutation и worker должны перечитать membership и
ownership под блокировками своего UoW; полученный grant нельзя сохранять между запросами
или использовать после commit. Project-qualified repositories и вызовы policy появятся
в BE-019/023/025/033; эти project routes всё ещё planned. Здесь verified только policy,
не объявлена работающая end-to-end object ACL до реализации этих routes/adapters.

## BE-018 verified auth regression

Atomic UPSERT проверен с24 concurrent attempts до/после DB window boundary;10 admitted
на каждое окно. Fixed windows намеренно допускают2×limit на границе (NFR), без rolling-window
гарантии. Используется statement_timestamp(), а не время начала transaction: ожидание
session lock/долгоживущая transaction не должны списывать попытку в уже прошедшее окно.
Login IP/email проверены раздельно (normalized email, socket IP, spoofed forwarded ignored).
Refresh31-й/32-й →429 с committed count, без rotation/revoke/cookie; абсолютный TTL сохранён.
Expired/revoked/disabled sessions не возобновляются через refresh. Replay/ACL regression — security suite.

Rate buckets старше24h удаляет bounded operator command `make auth-limits-cleanup`.
Он использует существующий environment приложения, удаляет до1000 rows, `FOR UPDATE SKIP LOCKED`,
statement timeout2s / lock timeout1s; результат removed=N. Никаких JWT/password/DB URLs в errors.
Отдельный CLI --max-rows1..10000; повторять вручную до removed=0 с учётом возможных locked rows.
Автоматического scheduler пока нет; запуск очистки — операционная обязанность до BE-032/047.
Auth session/history retention и общие anonymous/authenticated API quotas не объявляются
реализованными этим auth-specific review; внедряются при расширении runtime и BE-047/049.

## BE-020 existing-project ACL integrated

Project metadata endpoints используют policy BE-017 с context из actual projects/member rows.
Owner derived, editor/viewer только membership с совпадающими project/user IDs. List query
фильтрует owner OR current member в SQL; deleted только owner. Foreign/missing404 одинаковы,
visible forbidden403. Metadata GET join возвращает project + membership в одном SQL.

Перед mutation scalar ACL projection даёт deny ДО User locks: нельзя блокировать чужого
owner или отвечать503 вместо404/403 на denied operation. Затем user UUIDs(actor+owner) lock
sorted, actor session lock/recheck, project lock/populate_existing; membership/context заново
читаются и policy проверяется повторно. Revoked session401, lost membership404. Guarded RC,
SQL timeouts BE-019 сохраняются. Cross-owned edits не меняют глобальный lock order.


BE-023: readers list owner plus members. Only owner grants/changes; owner-or-self removes. Owner derived/immutable409; foreign/deleted404, visible forbidden403. Early policy before foreign user locks; locked fresh ACL/session recheck. Project row serializes member mutations and metadata CRUD. Max50 includes owner; duplicate409 MEMBER_EXISTS, unknown/inactive user404 USER_NOT_FOUND, cap429 MEMBER_LIMIT_EXCEEDED. No email/hash/session fields in responses. No project revision increment for membership changes.
