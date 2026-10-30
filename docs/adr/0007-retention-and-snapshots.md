# ADR-0007: История, snapshot и удаление

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](../tasks/ROADMAP.md).

## Контекст

DB и файловая система не имеют общей транзакции; сборка должна видеть неизменяемый input.

## Варианты

Полные копии при enqueue; ссылки на immutable revisions; чтение live tree.

## Решение

Snapshot entries pin revisions; soft-delete проекта7d; revisions/jobs30d; artifacts7d; audit90d. Consistent backup при maintenance barrier.

## Последствия и цена поддержки

Больше DB entries; pinned версии превышают обычный срок, но учитываются в quota. Binary revision restore не MVP, история bytes доступна.

## Критерий пересмотра

Реальное disk usage/ожидания undo требуют пересмотра retention и quota.

## Проверка

BE-003/006/007 проектируют; соответствующие implementation gates описаны в [карте](../tasks/ROADMAP.md). Решение draft, применение в продукте planned.
