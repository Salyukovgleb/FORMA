# Контракт с frontend

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

1. Login: access token/CSRF в память; credentials include для cookie routes.
2. GET projects → project_id; GET tree возвращает project_revision и nodes, строить дерево по parent_id.
3. GET file/content возвращает content revision; хранить её отдельно от Node metadata revision.
4. PUT content expected_revision; 200 обновляет локальную revision; 409 сохраняет несохранённый
текст и предлагает перечитать/сопоставить. Автоматическое слепое overwrite запрещено.
5. Перед compile получить актуальную project revision; POST compilations с новым Idempotency-Key;
202 job_id; polling GET job каждые 1s до 5s с jitter, на hidden tab 10s.
6. stage — coarse progress, не процент. Terminal succeeded → artifacts; failed → error_code,
logs; unknown file/line не подсвечивать как точную позицию.
7. Download через authenticated fetch, blob URL для PDF preview/Word download; Bearer не в URL.
Blob URL revoke при закрытии. CSP frontend ограничивает viewer; backend отдаёт nosniff/no-store.
8. Exports format=docx/zip тоже async. DOCX warnings из job.warnings и logs не скрывать.
9. DELETE project требует повторного ввода title и expected_revision; undo — restore до 7 суток.

На 401 очистить access, один coordinated refresh при наличии CSRF; replay/failed refresh → login.
После полной перезагрузки login требуется снова (ADR-0006). На 429 учитывать Retry-After;
POST создавать заново только с тем же idempotency key при неизвестном результате.
Без WebSocket/SSE. Контрактные fixture JSON в examples/; /docs только когда runtime реализован.

BE-015 transport implemented: login Origin обязателен; csrf_token держать в памяти,
refresh/logout с X-CSRF-Token и credentials include. Параллельный refresh координировать
между вкладками: второй запрос со старым token отзывает всю session. Cookie обновляется
только после commit; потерянный refresh response требует повторного login, grace нет.
Logout-all/revoke делают ранее выданные access JWT недействительными немедленно.

BE-016: профиль GET/PATCH `/api/v1/users/me` (Bearer). PATCH только display_name.
POST `/api/v1/users/me/change-password`: current_password/new_password, Bearer. Успех204
очищает refresh cookie и отзывает все сессии; удалить access/CSRF из памяти и показать login.
Неверный current401 не изменяет пароль/сессии, но клиент может показать общий auth error.

BE-019: POST /api/v1/projects (Bearer),201 Project DTO. Request title1..200 non-whitespace,
description≤2000 default empty, template_id null/omitted. Unicode/NUL validation, unknown fields422.
До BE-021 любой non-null template_id →404 NOT_FOUND (не игнорируется). Создаётся пустое дерево;
engine/main хранятся в DB с defaults и пока не входят в Project DTO (они в Settings BE-022).
Owner берётся из Principal, Cookie/owner_id/role не дают ownership. Квота retained active+deleted
100/user default, configurable MAX_PROJECTS_PER_USER;429 QUOTA_EXCEEDED, Retry-After86400 —
рекомендация повторить после cleanup, не обещание автоматического daily reset. Listing/read —BE-020.
503/потерянный ответ COMMIT может иметь uncertain outcome; не делать blind retry mutation,
проверить состояние после появления read/list или через оператора. Durable audit —BE-046.

BE-019 transient DB/row-lock contention →503 STORAGE_UNAVAILABLE, Retry-After1;
SQL lock timeout2s / statement timeout5s. Это не общий wall-clock deadline сетевого сбоя.

BE-020: GET list/search/detail, PATCH metadata, DELETE soft и POST restore implemented.
PATCH требует title, description и expected_revision; это контракт полного metadata update.
Readonly owner/role/status/main fields →422. PATCH revision+1; stale409 REVISION_CONFLICT
с details.current_revision. DELETE JSON confirm_title exact + expected_revision, success204;
wrong confirm409 INVALID_STATE, stale409, повтор DELETE deleted404 согласно visibility.
Restore owner-only: до7d включительно200/revision+1, active409, stale409, expired410 RETENTION_EXPIRED.
Deleted metadata/list виден только owner; PATCH deleted404. Soft-delete не освобождает retained
quota; physical purge/retention scheduler —BE-047. Cursor не переиспользовать с другими filters.


BE-023 API-034..037 implemented. POST normalized email+editor/viewer,201; PATCH role only,200; DELETE no body,204. Self-leave immediately removes visibility; repeating self-leave404. Owner grant/change/remove allowed except owner target409 OWNER_IMMUTABLE. Disabled/unknown email404 USER_NOT_FOUND.50 total cap429; no invitation email sent. Membership changes do not increment project revision. Jobs cancellation on revoke remains BE-037; durable audit BE-046.
