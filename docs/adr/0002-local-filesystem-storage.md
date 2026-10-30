# ADR-0002: Локальное immutable хранение

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](../tasks/ROADMAP.md).

## Контекст

Нужны версии, atomic saves, backup и отсутствие object store.

## Варианты

Mutable files; immutable blobs; object storage.

## Решение

UUID immutable revision/artifact blobs на persistent volume; DB metadata; shared/exclusive maintenance advisory lock.

## Последствия и цена поддержки

Один хост; публикация до DB commit оставляет orphan, GC убирает позже. Owner quota считает retained bytes.

## Критерий пересмотра

Multi-host requirement или measured disk throughput bottleneck.

## Проверка

BE-003/006/007 проектируют; соответствующие implementation gates описаны в [карте](../tasks/ROADMAP.md). Решение draft, применение в продукте planned.
