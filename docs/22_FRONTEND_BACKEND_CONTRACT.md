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
