"""Storage ports/value types. Logical names, MIME, ACL and metadata live in use cases."""

from dataclasses import dataclass
from enum import StrEnum
from typing import BinaryIO, Protocol
from uuid import UUID


class BlobArea(StrEnum):
    REVISIONS = "revisions"
    ARTIFACTS = "artifacts"


@dataclass(frozen=True)
class BlobKey:
    area: BlobArea
    id: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.area, BlobArea) or not isinstance(self.id, UUID):
            raise ValueError("Expected typed blob area and UUID")


@dataclass(frozen=True)
class StoredBlob:
    key: BlobKey
    size: int
    sha256: str


class StorageUnavailable(Exception):
    def __init__(self) -> None:
        super().__init__("STORAGE_UNAVAILABLE")


class MaintenanceBusy(StorageUnavailable):
    pass


class BlobNotFound(Exception):
    def __init__(self) -> None:
        super().__init__("NOT_FOUND")


class BlobTooLarge(Exception):
    def __init__(self) -> None:
        super().__init__("PAYLOAD_TOO_LARGE")


class StorageLease(Protocol):
    def check(self, *, exclusive: bool = False) -> None: ...


class BlobReferences(Protocol):
    def is_referenced(self, key: BlobKey) -> bool: ...


class FileStorage(Protocol):
    def publish(
        self,
        source: BinaryIO,
        lease: StorageLease,
        *,
        area: BlobArea = BlobArea.REVISIONS,
        max_bytes: int = 20 * 1024**2,
    ) -> StoredBlob: ...
    def open(self, key: BlobKey, lease: StorageLease) -> BinaryIO: ...
    def delete(self, key: BlobKey, lease: StorageLease, references: BlobReferences) -> bool: ...
