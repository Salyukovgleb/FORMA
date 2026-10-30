# Наблюдаемость

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

JSON logs stdout: timestamp,level,event,request_id,job_id,project_id,attempt,duration_ms,
error_code. Внешний X-Request-ID принимается только UUID; иначе generate. Stacktrace только
server error, с redaction. Путь из клиента и текст документа не логируются.
Audit mutation в той же DB transaction, payload whitelist action-specific IDs/counts;
login failures имеют actor_id nullable и entity_id=request_id. audit retention 90 суток.

Health live без DB; ready DB SELECT 1 + отдельная storage write probe, timeout 2s, generic status.
Worker heartbeat — в job, idle process logs heartbeat раз в 60s; scheduler latency и queue age
выводятся JSON summary раз в минуту. Metrics без нового сервера: counters/log summaries
HTTP p95, jobs by state, compile seconds, retries, expired leases, disk free, backup age.
Alert thresholds: oldest queued>5m, expired lease>60s, disk free<10%, failed backup>24h,
error rate>5%/5m. Первоначально оператор читает logs и системный scheduler reports.

## BE-010 implemented primitives

`forma_backend.core.logging`: configure_logging() настраивает только logger forma;
JsonFormatter использует whitelist event/IDs/counts/error codes и отбрасывает raw message,
args, arbitrary extras и exception text. request_context() принимает UUID либо генерирует новый,
сбрасывает ContextVar при выходе. HTTP integration — BE-012. Безопасный traceback formatter
пока не реализован: не передавать чувствительные сведения в сообщения сторонних logger.
