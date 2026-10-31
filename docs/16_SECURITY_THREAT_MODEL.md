# Модель угроз

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

Assets: исходники, пароли/session, ACL, целостность revisions, ресурсы хоста, backups.
Противник: anonymous client, злонамеренный участник/LaTeX, украденная session.
Trusted: API/use cases, PostgreSQL, storage publisher, sandbox controller и image supply chain.

| Угроза | Контроль | Доказательство до release |
|---|---|---|
| IDOR / guessed IDs | project-qualified lookups + ACL every request | SEC-API-001…046 |
| Role escalation / owner loss | owner derived, explicit member role enum | BE-023 concurrent tests |
| Path traversal / symlink | UUID physical keys, dirfd/no-follow, safe extractor | BE-024,028,034 |
| Malicious TeX / network read | per-attempt sandbox, no secrets/mount/socket | BE-034 cross-project sentinel/net probes |
| Fork bomb / disk fill | cgroup PID/mem/cpu, bounded tmpfs, timeout | BE-038 limits verified, no host impact |
| Refresh replay / CSRF | rotation history, cookie policy, Origin, CSRF | BE-018 simultaneous rotate/replay |
| Duplicate worker output | lease fencing and publish transaction | BE-032,035 stale worker test |
| Zip/XML bomb | archive limits, no entities, isolated parsers | BE-042,043 fixtures |
| Backup exposure | OS permissions 0700, encrypted destination, no credentials in dump logs | BE-047 restore drill |
| Dependency compromise | locked hashes, image digest, audit before release | BE-013,049 |

Auth rate-limit hashes IP with server HMAC, trust X-Forwarded-For только от configured proxy.
Без proxy используется socket peer. Не писать password/token/body в logs. Markdown/LaTeX/logs
в frontend только text rendering, не innerHTML. Swagger prod authenticated или disabled.
Residual risk: shared Linux kernel container escape; один хост — single failure domain;
локальный backup на том же диске не disaster recovery. Публичный запуск запрещён до BE-034/049.

BE-017: role/child-scope policy проверена против cross-project UUID, чужой membership,
подмены owner role, former requester и deleted visibility. Это unit/security evidence;
SEC project API tests и project-qualified DB lookup остаются gates BE-019/023/025.
