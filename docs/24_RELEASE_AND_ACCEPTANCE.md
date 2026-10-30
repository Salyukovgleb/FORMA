# Приёмка

Владелец: backend architect / backend-developer. Статус: draft. Обновлено: 2026-10-30.
Связи: BE-002–BE-007; ADR-0001–0007; проверки и задачи в [карте](tasks/ROADMAP.md).

M0: 26 документов, 46 методов с DTO/examples/ACL/tests, DDL+dictionary/ER, ADR, 52 cards/DAG,
self-review и честное evidence. Draft означает не approved; implementation остаётся planned.
M1: Compose/API/Postgres/worker стартуют, миграции и CI зелёные.
M2: register/login/projects/members; M3: tree/save/history/concurrency;
M4: проверенный sandbox + PDF; M5: DOCX structural fixtures + ZIP;
M6: full E2E, backup restore, нагрузка/security review, clean-room install.

DoR: вход/выход/ACL/DB impact известны, зависимости done, acceptance/negative tests заданы,
нет нерешённых архитектурных блокеров. DoD: code+docs+tests+local checks+SHA+push+PR+CI
для SHA+required review/merge+STATUS evidence. Awaiting review не done.
Release candidate не допускается без успешного BE-034/038/047/049/051. Версия 0.1.0 после
BE-052, tag только на проверенный merge SHA, rollback совместимой версии без destructive DB undo.
