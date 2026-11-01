# Лимиты и NFR

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

Начальные эксплуатационные defaults, менять через конфигурацию с startup validation.

| Ограничение | Значение | Контроль |
|---|---|---|
| API JSON | 2 MiB; текст ≤1 MiB UTF-8 | до parse + после encoding |
| Upload | 20 MiB | streaming byte counter |
| Project / owner retained storage | 500 MiB / 2 GiB | owner+project locks, SUM revisions/artifacts |
| Projects / user; members / project | 100 / 50 | транзакционная квота |
| Live tree | 2000 nodes, depth20, path1024 | parent check, bounded query |
| Jobs pending+running | requester3, project3, global pending100 | scheduler/user locks |
| Running | global1 default, project1 | scheduler advisory lock |
| PDF / DOCX / ZIP wall time | 60s / 120s / 30s | kill sandbox |
| Sandbox | 1 CPU, 1 GiB RAM, 64 PID, work512 MiB | rootless cgroup v2 + tmpfs |
| Artifact | 100 MiB | bounded collection |
| Register/login | IP 10/15min; login email 10/15min | PostgreSQL atomic bucket |
| Refresh | session 30/min | atomic bucket |
| Authenticated API | user 300/min | atomic bucket |
| Upload | user 20/min | atomic bucket |
| Compile/export | user 10/min | atomic bucket + job quota |
| Logs | 1000 entries / 1 MiB | truncate marker |

Fixed-window rate limits, clock DB; UPSERT count атомарный, очистка buckets >24h.
Граница окна допускает burst 2×limit, принято для MVP. Anonymous API IP 120/min кроме probes;
health на приватной ingress сети. Concurrency hash CPU ограничивается thread semaphore.

Целевые SLO (не измеренные): metadata p95<300ms при 20 активных пользователях на 4 CPU/8 GiB SSD;
20 параллельных saves без потерь; queued job pick-up≤2s без занятых slots. TeX latency зависит
от документа. No N+1; immutable download streaming 64 KiB chunks. Размер backing volume
≥20 GiB для dev smoke, production capacity планировать по actual retained data + backup.

BE-018: auth-specific limits verified на real PostgreSQL (register/login, refresh и password-change).
DB clock для bucket — statement_timestamp(), включая transaction, начавшуюся в прошлом окне.
Очистка >24h реализована operator CLI, bounded rows + timeouts; автоматический запуск ещё planned.
Общие anonymous120/min и authenticated300/min, upload/compile quotas остаются planned;
не считать эту таблицу доказательством реализации всего NFR в текущем identity runtime.

BE-019: Projects/user quota100 default на retained active+deleted rows. Startup validation
MAX_PROJECTS_PER_USER1..10000, серверная настройка; не request parameter. User lock сериализует
две different-session creations у границы99/100; soft-delete не освобождает слот до purge.
Member quota50 и общие user/API limits ещё planned. Error quota429 не является fixed-window reset.

CreateProject SQL work ограничен lock_timeout2s и statement_timeout5s; operational DB errors
переводятся в503 после rollback/guard teardown, programming/integrity errors не маскируются
этой классификацией (ошибка на guarded commit остаётся safe503 с возможным uncertain outcome).

CreateProject UoW явно использует READ COMMITTED независимо от server/engine default:
после ожидания user lock count видит предыдущий commit. Regression проверяет concurrent
different-session quota при исходных READ COMMITTED и REPEATABLE READ defaults.

BE-020: один project/membership SQL на страницу, без per-project lookup, page size≤100.
Это проверка query count, не benchmark p95. Cross-user UUID locks sorted, SQL deadlines
и8 guard slots сохраняются. Search/ACL EXPLAIN/performance —BE-048.
