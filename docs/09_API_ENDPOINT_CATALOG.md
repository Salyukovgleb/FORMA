# Каталог API

Владелец: backend architect. Статус: draft. Обновлено: 2026-10-30. Состояние реализации указано для каждого метода.

Всего **46** методов: 13 implemented (health/identity/projects), 33 planned. Базовый префикс /api/v1, health без него.

| ID | Метод | DTO | ACL | Задача |
|---|---|---|---|---|
| API-001 | `GET /health/live` | — → Health | public | BE-012 |
| API-002 | `GET /health/ready` | — → Health | public | BE-012 |
| API-003 | `POST /api/v1/auth/register` | Register → Profile | public | BE-014 |
| API-004 | `POST /api/v1/auth/login` | Login → Token | public | BE-015 |
| API-005 | `POST /api/v1/auth/refresh` | — → Token | refresh | BE-015 |
| API-006 | `POST /api/v1/auth/logout` | — → 204 | refresh | BE-015 |
| API-007 | `POST /api/v1/auth/logout-all` | — → 204 | authenticated | BE-015 |
| API-008 | `GET /api/v1/users/me` | — → Profile | authenticated | BE-016 |
| API-009 | `PATCH /api/v1/users/me` | ProfilePatch → Profile | authenticated | BE-016 |
| API-010 | `POST /api/v1/users/me/change-password` | PasswordChange → 204 | authenticated | BE-016 |
| API-011 | `GET /api/v1/auth/sessions` | — → Page_Session_ | authenticated | BE-015 |
| API-012 | `DELETE /api/v1/auth/sessions/{session_id}` | — → 204 | authenticated | BE-015 |
| API-013 | `GET /api/v1/projects` | — → Page_Project_ | authenticated | BE-020 |
| API-014 | `POST /api/v1/projects` | ProjectCreate → Project | authenticated | BE-019 |
| API-015 | `GET /api/v1/projects/{project_id}` | — → Project | reader | BE-020 |
| API-016 | `PATCH /api/v1/projects/{project_id}` | ProjectPatch → Project | writer | BE-020 |
| API-017 | `DELETE /api/v1/projects/{project_id}` | DeleteProject → 204 | owner | BE-020 |
| API-018 | `POST /api/v1/projects/{project_id}/restore` | RestoreProject → Project | owner | BE-020 |
| API-019 | `GET /api/v1/projects/{project_id}/settings` | — → Settings | reader | BE-022 |
| API-020 | `PATCH /api/v1/projects/{project_id}/settings` | SettingsPatch → Settings | writer | BE-022 |
| API-021 | `GET /api/v1/projects/{project_id}/tree` | — → Tree | reader | BE-025 |
| API-022 | `POST /api/v1/projects/{project_id}/folders` | FolderCreate → Node | writer | BE-025 |
| API-023 | `POST /api/v1/projects/{project_id}/files` | FileCreate → Node | writer | BE-025 |
| API-024 | `POST /api/v1/projects/{project_id}/uploads` | Upload → Node | writer | BE-026 |
| API-025 | `GET /api/v1/projects/{project_id}/nodes/{node_id}` | — → Node | reader | BE-025 |
| API-026 | `GET /api/v1/projects/{project_id}/files/{file_id}/content` | — → Content | reader | BE-027 |
| API-027 | `PUT /api/v1/projects/{project_id}/files/{file_id}/content` | SaveContent → Content | writer | BE-027 |
| API-028 | `PATCH /api/v1/projects/{project_id}/nodes/{node_id}` | NodePatch → Node | writer | BE-028 |
| API-029 | `DELETE /api/v1/projects/{project_id}/nodes/{node_id}` | — → 204 | writer | BE-028 |
| API-030 | `GET /api/v1/projects/{project_id}/files/{file_id}/download` | — → Binary | reader | BE-026 |
| API-031 | `GET /api/v1/projects/{project_id}/files/{file_id}/revisions` | — → Page_FileRevision_ | reader | BE-029 |
| API-032 | `GET /api/v1/projects/{project_id}/files/{file_id}/revisions/{revision}` | — → Binary | reader | BE-029 |
| API-033 | `POST /api/v1/projects/{project_id}/files/{file_id}/revisions/{revision}/restore` | RestoreRevision → Content | writer | BE-029 |
| API-034 | `GET /api/v1/projects/{project_id}/members` | — → Members | reader | BE-023 |
| API-035 | `POST /api/v1/projects/{project_id}/members` | MemberAdd → Member | owner | BE-023 |
| API-036 | `PATCH /api/v1/projects/{project_id}/members/{user_id}` | MemberPatch → Member | owner | BE-023 |
| API-037 | `DELETE /api/v1/projects/{project_id}/members/{user_id}` | — → 204 | owner_or_self | BE-023 |
| API-038 | `POST /api/v1/projects/{project_id}/compilations` | Compile → JobAccepted | writer | BE-037 |
| API-039 | `POST /api/v1/projects/{project_id}/exports` | Export → JobAccepted | reader | BE-044 |
| API-040 | `GET /api/v1/projects/{project_id}/jobs` | — → Page_Job_ | reader | BE-037 |
| API-041 | `GET /api/v1/projects/{project_id}/jobs/{job_id}` | — → Job | reader | BE-037 |
| API-042 | `GET /api/v1/projects/{project_id}/jobs/{job_id}/logs` | — → Page_JobLog_ | reader | BE-037 |
| API-043 | `POST /api/v1/projects/{project_id}/jobs/{job_id}/cancel` | — → JobAccepted | owner_or_requester | BE-037 |
| API-044 | `GET /api/v1/projects/{project_id}/artifacts/{artifact_id}/download` | — → Binary | reader | BE-037 |
| API-045 | `GET /api/v1/templates` | — → Templates | authenticated | BE-021 |
| API-046 | `GET /api/v1/templates/{template_id}` | — → Template | authenticated | BE-021 |

Полные спецификации: [system](api/system.md), [identity](api/identity.md), [projects](api/projects.md), [project-files](api/project-files.md), [access](api/access.md), [documents](api/documents.md), [jobs](api/jobs.md).

[OpenAPI](contracts/openapi.json) · [Pydantic](contracts/models.py) · [реестр связей](contracts/endpoints.json).
