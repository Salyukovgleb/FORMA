# ADR-0004: Изоляция документов

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](../tasks/ROADMAP.md).

## Контекст

TeX/Pandoc/OOXML parsers исполняют недоверенный ввод; worker с secrets не sandbox.

## Варианты

Обычный subprocess; per-attempt rootless container; VM sandbox.

## Решение

Linux cgroup v2 rootless Docker per attempt с tmpfs bounds, no network/secrets/socket; trusted controller host process. Dev Compose worker-controller монтирует rootless socket только для разработки.

## Последствия и цена поддержки

Нужны systemd cgroup delegation, image pinning и реальные adversarial tests. Shared kernel risk остаётся; launch fail closed. Host controller видит абсолютный job input path; не путать host path с container volume path.

## Критерий пересмотра

Невозможность подтвердить limits или неприемлемый shared-kernel risk → ADR VM, публичный запуск заблокирован.

## Проверка

BE-003/006/007 проектируют; соответствующие implementation gates описаны в [карте](../tasks/ROADMAP.md). Решение draft, применение в продукте planned.
