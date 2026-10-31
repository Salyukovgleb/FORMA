"""POSIX private immutable blobs, descriptor-relative paths and guarded GC (ADR-0009)."""

import hashlib
import os
import stat
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from time import time
from typing import BinaryIO
from uuid import UUID, uuid4

from forma_backend.modules.project_files.storage import (
    BlobArea,
    BlobKey,
    StoredBlob,
    StorageLease,
    BlobReferences,
    StorageUnavailable,
    BlobNotFound,
    BlobTooLarge,
)

DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
CREATE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW


def identity(fd: int) -> tuple[int, int]:
    value = os.fstat(fd)
    return value.st_dev, value.st_ino


def same_entry(directory: int, name: str, fd: int) -> bool:
    try:
        value = os.stat(name, dir_fd=directory, follow_symlinks=False)
        return (value.st_dev, value.st_ino) == identity(fd)
    except FileNotFoundError:
        return False


def private_file(fd: int) -> os.stat_result:
    value = os.fstat(fd)
    if (
        not stat.S_ISREG(value.st_mode)
        or value.st_nlink != 1
        or value.st_uid != os.geteuid()
        or value.st_mode & 0o077
    ):
        raise StorageUnavailable()
    return value


class LocalFileStorage:
    def __init__(
        self,
        root: Path,
        *,
        min_free_bytes: int = 2 * 1024**3,
        min_free_ratio: float = 0.1,
    ) -> None:
        if not root.is_absolute() or ".." in root.parts:
            raise ValueError("Expected absolute storage root without traversal")
        if min_free_bytes < 0 or not 0 <= min_free_ratio < 1:
            raise ValueError("Invalid storage capacity floor")
        self._root = root
        self._min_free_bytes = min_free_bytes
        self._min_free_ratio = min_free_ratio
        self._identities: dict[str, tuple[int, int]] = {}
        with self._directories(initialize=True):
            pass

    @contextmanager
    def _directories(self, *, initialize: bool = False) -> Iterator[dict[str, int]]:
        try:
            with ExitStack() as stack:

                def track(fd: int) -> int:
                    stack.callback(os.close, fd)
                    return fd

                root = track(os.open("/", DIRECTORY_FLAGS))
                for component in self._root.parts[1:]:
                    root = track(os.open(component, DIRECTORY_FLAGS, dir_fd=root))
                directories = {"root": root}
                for name in ["root", "revisions", "artifacts", "temp"]:
                    if name != "root":
                        if initialize:
                            try:
                                os.mkdir(name, 0o700, dir_fd=root)
                            except FileExistsError:
                                pass
                        directories[name] = track(os.open(name, DIRECTORY_FLAGS, dir_fd=root))
                    fd = directories[name]
                    value = os.fstat(fd)
                    if value.st_uid != os.geteuid() or value.st_mode & 0o022:
                        raise StorageUnavailable()
                    if initialize:
                        self._identities[name] = identity(fd)
                    if (
                        identity(fd) != self._identities[name]
                        or value.st_dev != os.fstat(root).st_dev
                    ):
                        raise StorageUnavailable()
                if initialize:
                    os.fsync(root)
                yield directories
        except OSError:
            raise StorageUnavailable() from None

    def _capacity(self, directory: int) -> None:
        space = os.fstatvfs(directory)
        free = space.f_bavail * space.f_frsize
        if free < self._min_free_bytes or space.f_bavail < space.f_blocks * self._min_free_ratio:
            raise StorageUnavailable()

    def _visible(self, directories: dict[str, int]) -> None:
        # Reopen the configured root as well: an anchored but detached root is not publishable.
        with self._directories():
            pass
        for name in ["revisions", "artifacts", "temp"]:
            if not same_entry(directories["root"], name, directories[name]):
                raise StorageUnavailable()

    def publish(
        self,
        source: BinaryIO,
        lease: StorageLease,
        *,
        area: BlobArea = BlobArea.REVISIONS,
        max_bytes: int = 20 * 1024**2,
    ) -> StoredBlob:
        if not isinstance(area, BlobArea) or not 1 <= max_bytes <= 100 * 1024**2:
            raise ValueError("Invalid publication area/limit")
        lease.check()
        with self._directories() as directories:
            temporary, destination = directories["temp"], directories[area.value]
            self._capacity(destination)
            name = str(uuid4())
            staged: int | None = None
            reserved: int | None = None
            try:
                staged = os.open(name, CREATE_FLAGS, 0o600, dir_fd=temporary)
                size = 0
                checksum = hashlib.sha256()
                while True:
                    chunk = source.read(65536)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > max_bytes:
                        raise BlobTooLarge()
                    checksum.update(chunk)
                    pending = memoryview(chunk)
                    while pending:
                        written = os.write(staged, pending)
                        if written <= 0:
                            raise StorageUnavailable()
                        pending = pending[written:]
                os.fsync(staged)
                private_file(staged)
                lease.check()
                self._visible(directories)
                reserved = os.open(name, CREATE_FLAGS, 0o600, dir_fd=destination)
                if not same_entry(temporary, name, staged) or not same_entry(
                    destination, name, reserved
                ):
                    raise StorageUnavailable()
                os.rename(name, name, src_dir_fd=temporary, dst_dir_fd=destination)
                os.fsync(destination)
                os.fsync(temporary)
                if not same_entry(destination, name, staged):
                    raise StorageUnavailable()
                self._visible(directories)
                lease.check()
                return StoredBlob(BlobKey(area, UUID(name)), size, checksum.hexdigest())
            except OSError:
                raise StorageUnavailable() from None
            finally:
                # Only remove entries still pointing to our private staging/reservation inode.
                for directory, fd in [(temporary, staged), (destination, reserved)]:
                    if fd is not None:
                        try:
                            if same_entry(directory, name, fd):
                                os.unlink(name, dir_fd=directory)
                        except OSError:
                            pass  # Crash-safe orphan, never a DB reference.
                        finally:
                            os.close(fd)

    def open(self, key: BlobKey, lease: StorageLease) -> BinaryIO:
        lease.check()
        with self._directories() as directories:
            try:
                fd = os.open(str(key.id), READ_FLAGS, dir_fd=directories[key.area.value])
            except FileNotFoundError:
                raise BlobNotFound() from None
            try:
                private_file(fd)
                self._visible(directories)
                lease.check()
                return os.fdopen(fd, "rb")
            except BaseException:
                os.close(fd)
                raise

    def delete(self, key: BlobKey, lease: StorageLease, references: BlobReferences) -> bool:
        lease.check(exclusive=True)
        with self._directories() as directories:
            directory = directories[key.area.value]
            try:
                fd = os.open(str(key.id), READ_FLAGS, dir_fd=directory)
            except FileNotFoundError:
                return False
            try:
                value = private_file(fd)
                if time() - value.st_mtime <= 86400:
                    return False
                referenced = references.is_referenced(key)
                if type(referenced) is not bool:
                    raise StorageUnavailable()
                if referenced:
                    return False
                lease.check(exclusive=True)
                self._visible(directories)
                if not same_entry(directory, str(key.id), fd):
                    raise StorageUnavailable()
                os.unlink(str(key.id), dir_fd=directory)
                os.fsync(directory)
                return True
            finally:
                os.close(fd)

    def collect_temp(self, lease: StorageLease, *, max_files: int = 1000) -> int:
        if not 1 <= max_files <= 10000:
            raise ValueError("Invalid staging GC limit")
        lease.check(exclusive=True)
        removed = 0
        with self._directories() as directories:
            directory = directories["temp"]
            with os.scandir(directory) as entries:
                for index, entry in enumerate(entries):
                    if index >= max_files:
                        break
                    try:
                        if str(UUID(entry.name)) != entry.name:
                            continue
                    except ValueError:
                        continue
                    try:
                        fd = os.open(entry.name, READ_FLAGS, dir_fd=directory)
                    except FileNotFoundError:
                        continue
                    try:
                        value = private_file(fd)
                        if time() - value.st_mtime <= 86400:
                            continue
                        lease.check(exclusive=True)
                        self._visible(directories)
                        if not same_entry(directory, entry.name, fd):
                            raise StorageUnavailable()
                        os.unlink(entry.name, dir_fd=directory)
                        removed += 1
                    finally:
                        os.close(fd)
            if removed:
                os.fsync(directory)
        return removed
