# ADR-0006: Auth transport и минимальные зависимости

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](../tasks/ROADMAP.md).

## Контекст

Нужны безопасные hashes/JWT/rotation без auth service.

## Варианты

Opaque access; JWT; внешняя identity платформа.

## Решение

JWT access 10m с session DB check, opaque refresh cookie30d, CSRF token в памяти, scrypt stdlib. PyJWT для JWT, psycopg для PostgreSQL; openapi-spec-validator только tooling.

## Последствия и цена поддержки

JWT не устраняет DB lookup; reload требует login из-за отсутствия persisted CSRF. OAuth/email recovery вне MVP. Не реализовывать криптопримитивы вручную.

## Критерий пересмотра

Требуется silent reload login или внешний SSO; изменить контракт через ADR до code.

## Проверка

BE-003/006/007 проектируют; соответствующие implementation gates описаны в [карте](../tasks/ROADMAP.md). Решение draft, применение в продукте planned.
