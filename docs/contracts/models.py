"""Phase A wire contracts only. No application handlers or database adapters."""

from forma_backend.modules.identity.schemas import (
    Register as Register,
    Profile as Profile,
    Email as Email,
    Password as Password,
)
from forma_backend.modules.identity.session_schemas import (
    Login as Login,
    Token as Token,
    Session as Session,
)
from forma_backend.modules.identity.profile_schemas import (
    ProfilePatch as ProfilePatch,
    PasswordChange as PasswordChange,
)
from forma_backend.modules.projects.schemas import (
    Project as Project,
    ProjectCreate as ProjectCreate,
)
from forma_backend.core.contracts import Page as Page
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID
from pydantic import Field
from forma_backend.core.contracts import (
    DTO as DTO,
    ErrorDetail as ErrorDetail,
    Error as Error,
    ErrorEnvelope as ErrorEnvelope,
    Health as Health,
)

Name = Annotated[str, Field(min_length=1, max_length=255)]
Revision = Annotated[int, Field(ge=1)]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Engine = Literal["pdflatex", "xelatex", "lualatex"]
Role = Literal["owner", "editor", "viewer"]
State = Literal["queued", "running", "retry_wait", "succeeded", "failed", "cancelled"]


class ProjectPatch(DTO):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    description: Annotated[str, Field(max_length=2000)]
    expected_revision: Revision


class Settings(DTO):
    main_file_id: UUID | None
    engine: Engine
    revision: Revision


class SettingsPatch(DTO):
    main_file_id: UUID | None
    engine: Engine
    expected_revision: Revision


class DeleteProject(DTO):
    confirm_title: str
    expected_revision: Revision


class RestoreProject(DTO):
    expected_revision: Revision


class FolderCreate(DTO):
    parent_id: UUID | None = None
    name: Name


class FileCreate(FolderCreate):
    content: Annotated[str, Field(max_length=1048576)] = ""


class Upload(DTO):
    parent_id: UUID | None = None
    file: Annotated[bytes, Field(json_schema_extra={"format": "binary"})]


class Node(DTO):
    id: UUID
    project_id: UUID
    parent_id: UUID | None
    name: str
    node_type: Literal["file", "folder"]
    logical_path: str
    media_type: str | None
    size_bytes: int
    content_hash: Sha256 | None
    content_revision: Revision | None
    revision: Revision
    created_at: datetime
    updated_at: datetime


class Tree(DTO):
    project_revision: Revision
    nodes: list[Node]


class NodePatch(DTO):
    name: Name
    parent_id: UUID | None
    expected_revision: Revision


class Content(DTO):
    file_id: UUID
    revision: Revision
    content: str
    content_hash: Sha256


class SaveContent(DTO):
    content: Annotated[str, Field(max_length=1048576)]
    expected_revision: Revision


class RestoreRevision(DTO):
    expected_revision: Revision


class FileRevision(DTO):
    revision: Revision
    content_hash: Sha256
    size_bytes: int
    author_id: UUID
    created_at: datetime


class MemberAdd(DTO):
    email: Email
    role: Literal["editor", "viewer"]


class MemberPatch(DTO):
    role: Literal["editor", "viewer"]


class Member(DTO):
    user_id: UUID
    display_name: str
    role: Role
    created_at: datetime


class Compile(DTO):
    expected_project_revision: Revision


class Export(Compile):
    format: Literal["docx", "zip"]
    reference_id: Literal["forma-default-v1"] = "forma-default-v1"


class JobAccepted(DTO):
    job_id: UUID
    state: State
    project_revision: Revision


class Artifact(DTO):
    id: UUID
    artifact_type: Literal["pdf", "docx", "zip"]
    filename: str
    mime_type: str
    size_bytes: int
    sha256: Sha256
    expires_at: datetime


class JobLog(DTO):
    sequence: int
    level: Literal["info", "warning", "error"]
    code: str
    message: str
    file: str | None
    line: int | None
    created_at: datetime


class Job(DTO):
    id: UUID
    project_id: UUID
    requested_by: UUID
    job_type: Literal["pdf", "docx", "zip"]
    state: State
    stage: Literal["waiting", "snapshot", "processing", "publishing", "complete"]
    attempt: int
    project_revision: Revision
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    cancellation_requested: bool
    error_code: str | None
    artifacts: list[Artifact]
    warnings: Annotated[list[JobLog], Field(max_length=100)]


class Template(DTO):
    id: str
    title: str
    description: str
    engine: Engine
    main_file: str
    files: list[str]
    version: str


class Members(DTO):
    items: list[Member]


class Templates(DTO):
    items: list[Template]


class Binary(DTO):
    """Transport descriptor, bytes are streamed without JSON envelope."""

    content: bytes
