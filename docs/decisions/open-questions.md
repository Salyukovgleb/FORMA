# Открытые вопросы и release blockers

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](../tasks/ROADMAP.md).

| Вопрос | Принятое проектное решение | Кто/когда проверяет |
|---|---|---|
| Есть ли cgroup delegation/rootless на deployment host? | Linux target, fail closed | operator + BE-034, до публичного запуска |
| Приемлем ли shared-kernel risk? | rootless per-job isolation | owner + BE-049 security review |
| Достаточен ли DOCX subset для реальных документов? | Матрица в 13_DOCX_EXPORT | product owner + BE-039/045 |
| Где хранить disaster-recovery backup? | Отдельный encrypted диск/host | operator + BE-047, до user data |
| Как обеспечить account recovery без email? | Административная процедура, no public reset endpoint | owner до публичного запуска |
| main сейчас без защиты (GitHub API protected=false). Кто настраивает protection? | PR+green SHA checks, без self-merge в фазе A | repo admin до M1 |

Эти вопросы не оставляют неоднозначных SQL/API решений; они ограничивают deployment/release.
Масштаб и latency targets предварительные до BE-048. Не заявлять выполненные sandbox,
реальные PDF/DOCX или restore на основании одной спецификации.
