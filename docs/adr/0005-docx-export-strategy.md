# ADR-0005: DOCX из исходников

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](../tasks/ROADMAP.md).

## Контекст

Word должен быть редактируемым; PDF теряет структуру.

## Варианты

Pandoc LaTeX→DOCX; PDF→Word; собственный TeX parser.

## Решение

Pandoc + bounded include resolver + versioned reference.docx + python-docx, всё в sandbox.

## Последствия и цена поддержки

Ограниченное subset, warnings и structural golden tests; нет обещания pixel fidelity.

## Критерий пересмотра

Подтверждённые пользовательские документы не покрываются subset и есть бюджет специализированного handler.

## Проверка

BE-003/006/007 проектируют; соответствующие implementation gates описаны в [карте](../tasks/ROADMAP.md). Решение draft, применение в продукте planned.
