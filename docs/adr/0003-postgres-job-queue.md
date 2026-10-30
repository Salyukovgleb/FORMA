# ADR-0003: Очередь PostgreSQL

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](../tasks/ROADMAP.md).

## Контекст

Job retries/leases/idempotency нужны без broker.

## Варианты

PostgreSQL row locks; Redis/Celery; in-memory background tasks.

## Решение

SKIP LOCKED claim, lease token fencing, bounded retry, periodic reaper и default one worker slot.

## Последствия и цена поддержки

Delivery at least once; publication effectively once по DB fence. DB load и polling учитываются в capacity.

## Критерий пересмотра

Измеренные queue latency/DB contention при исчерпанном tuning.

## Проверка

BE-003/006/007 проектируют; соответствующие implementation gates описаны в [карте](../tasks/ROADMAP.md). Решение draft, применение в продукте planned.
