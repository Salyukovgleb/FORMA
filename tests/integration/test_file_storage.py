"""Storage security/fault tests use disposable PostgreSQL and private temporary directories."""

import errno
import hashlib
import io
import os
import stat
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
import time

import pytest
from sqlalchemy import text

from forma_backend.infrastructure.database.session import create_database_engine
from forma_backend.infrastructure.storage.local import LocalFileStorage
from forma_backend.infrastructure.storage.maintenance import MaintenanceGuard
from forma_backend.modules.project_files.storage import (
    BlobArea,
    BlobKey,
    BlobTooLarge,
    BlobNotFound,
    StorageUnavailable,
    MaintenanceBusy,
)


@pytest.fixture
def storage(database_url, tmp_path):
    engine = create_database_engine(database_url)
    # Capacity is tested separately; host free space must not affect fault/security tests.
    local = LocalFileStorage(tmp_path, min_free_bytes=0, min_free_ratio=0)
    try:
        yield local, engine, tmp_path
    finally:
        engine.dispose()


class References:
    def __init__(self, *keys):
        self.keys = set(keys)

    def is_referenced(self, key):
        return key in self.keys


def age(path):
    past = (datetime.now(UTC) - timedelta(hours=25)).timestamp()
    os.utime(path, (past, past))


def await_backend_exit(engine, pid):
    # PQfinish/socket close is asynchronous at the server; prove exit, don't assume a delay.
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        with engine.connect() as db:
            live = db.scalar(
                text("SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE pid=:pid)"), {"pid": pid}
            )
        if not live:
            return
        time.sleep(0.01)
    raise AssertionError("Guard backend did not exit")


@pytest.mark.parametrize("area", list(BlobArea))
def test_publish_private_immutable_bytes_and_stream_open(storage, area):
    local, engine, root = storage
    payload = b"source\x00binary\n" * 12000
    with MaintenanceGuard(engine) as lease:
        blob = local.publish(io.BytesIO(payload), lease, area=area)
        assert isinstance(blob.key.id, UUID) and blob.key.area == area
        assert blob.size == len(payload) and blob.sha256 == hashlib.sha256(payload).hexdigest()
        with local.open(blob.key, lease) as handle:
            assert handle.read() == payload
        path = root / area.value / str(blob.key.id)
        assert stat.S_IMODE(path.stat().st_mode) == 0o600 and path.stat().st_nlink == 1
        assert list((root / "temp").iterdir()) == []


@pytest.mark.parametrize("bad", ["../escape", "/tmp/escape", "x/y", "x\\y", "\x00", "not-uuid"])
def test_physical_keys_reject_strings_before_io(bad):
    with pytest.raises(ValueError):
        BlobKey(BlobArea.REVISIONS, bad)
    with pytest.raises(ValueError):
        BlobKey(bad, uuid4())


def test_collision_preserves_existing_blob(storage, monkeypatch):
    from forma_backend.infrastructure.storage import local as module

    local, engine, root = storage
    identifier = uuid4()
    (root / "revisions" / str(identifier)).write_bytes(b"existing")
    os.chmod(root / "revisions" / str(identifier), 0o600)
    monkeypatch.setattr(module, "uuid4", lambda: identifier)
    with MaintenanceGuard(engine) as lease:
        with pytest.raises(StorageUnavailable):
            local.publish(io.BytesIO(b"replacement"), lease)
    assert (root / "revisions" / str(identifier)).read_bytes() == b"existing"
    assert list((root / "temp").iterdir()) == []


@pytest.mark.parametrize("fault", ["enospc", "zero-write", "fsync", "rename"])
def test_write_and_publish_faults_never_return_a_reference(storage, monkeypatch, fault):
    from forma_backend.infrastructure.storage import local as module

    local, engine, root = storage

    def failed(*args, **kwargs):
        if fault == "zero-write":
            return 0
        raise OSError(errno.ENOSPC, "private-sentinel-path")

    target = {"enospc": "write", "zero-write": "write", "fsync": "fsync", "rename": "rename"}[fault]
    with MaintenanceGuard(engine) as lease:
        with monkeypatch.context() as patched:
            patched.setattr(module.os, target, failed)
            with pytest.raises(StorageUnavailable) as error:
                local.publish(io.BytesIO(b"unpublished"), lease)
        assert "private-sentinel" not in str(error.value)
    assert list((root / "temp").iterdir()) == []
    assert list((root / "revisions").iterdir()) == []


def test_partial_writes_and_payload_limit(storage, monkeypatch):
    from forma_backend.infrastructure.storage import local as module

    local, engine, root = storage
    original = os.write
    monkeypatch.setattr(module.os, "write", lambda fd, data: original(fd, data[:3]))
    with MaintenanceGuard(engine) as lease:
        blob = local.publish(io.BytesIO(b"several partial writes"), lease)
        with local.open(blob.key, lease) as handle:
            assert handle.read() == b"several partial writes"
        with pytest.raises(BlobTooLarge):
            local.publish(io.BytesIO(b"too many"), lease, max_bytes=3)
    assert list((root / "temp").iterdir()) == []
    assert len(list((root / "revisions").iterdir())) == 1


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo"])
def test_non_regular_or_linked_blobs_are_rejected(storage, tmp_path, kind):
    local, engine, root = storage
    key = BlobKey(BlobArea.REVISIONS, uuid4())
    outside = tmp_path / "outside-sentinel"
    outside.write_bytes(b"outside")
    os.chmod(outside, 0o600)
    path = root / "revisions" / str(key.id)
    if kind == "symlink":
        path.symlink_to(outside)
    elif kind == "hardlink":
        os.link(outside, path)
    else:
        os.mkfifo(path)
    with MaintenanceGuard(engine) as lease:
        with pytest.raises(StorageUnavailable):
            local.open(key, lease)
    assert outside.read_bytes() == b"outside"


def test_directory_swap_cannot_escape_root(storage, tmp_path):
    local, engine, root = storage
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "revisions").rename(root / "old-revisions")
    (root / "revisions").symlink_to(outside, target_is_directory=True)
    with MaintenanceGuard(engine) as lease:
        with pytest.raises(StorageUnavailable):
            local.publish(io.BytesIO(b"escaped"), lease)
    assert list(outside.iterdir()) == []


def test_capacity_floor_and_ratio_are_checked(storage, monkeypatch):
    from forma_backend.infrastructure.storage import local as module
    from types import SimpleNamespace

    _, engine, root = storage
    local = LocalFileStorage(root)
    for available, total in [(1024, 10000), (3 * 1024**3, 100 * 1024**3)]:
        fake = SimpleNamespace(f_bavail=available, f_blocks=total, f_frsize=1)
        with MaintenanceGuard(engine) as lease, monkeypatch.context() as patched:
            patched.setattr(module.os, "fstatvfs", lambda fd: fake)
            with pytest.raises(StorageUnavailable):
                local.publish(io.BytesIO(b"no space"), lease)
    assert list((root / "revisions").iterdir()) == []


def test_gc_preserves_references_fresh_blobs_and_requires_exclusive_guard(storage):
    local, engine, root = storage
    with MaintenanceGuard(engine) as lease:
        kept = local.publish(io.BytesIO(b"referenced"), lease)
        old = local.publish(io.BytesIO(b"orphan"), lease)
        fresh = local.publish(io.BytesIO(b"fresh"), lease)
        with pytest.raises(StorageUnavailable):
            local.delete(old.key, lease, References())
    for blob in [kept, old]:
        age(root / blob.key.area.value / str(blob.key.id))
    with MaintenanceGuard(engine, exclusive=True) as lease:
        refs = References(kept.key)
        assert not local.delete(kept.key, lease, refs)
        assert not local.delete(fresh.key, lease, refs)
        assert local.delete(old.key, lease, refs)
        assert not local.delete(old.key, lease, refs)
        with local.open(kept.key, lease) as handle:
            assert handle.read() == b"referenced"
        with pytest.raises(BlobNotFound):
            local.open(old.key, lease)


def test_staging_gc_only_old_uuid_regular_files(storage):
    local, engine, root = storage
    old = root / "temp" / str(uuid4())
    old.write_bytes(b"crashed staging")
    os.chmod(old, 0o600)
    age(old)
    fresh = root / "temp" / str(uuid4())
    fresh.write_bytes(b"active")
    os.chmod(fresh, 0o600)
    sentinel = root / "temp" / "non-uuid"
    sentinel.write_bytes(b"unknown")
    with MaintenanceGuard(engine, exclusive=True) as lease:
        assert local.collect_temp(lease, max_files=100) == 1
    assert not old.exists() and fresh.exists() and sentinel.exists()


def test_shared_publishers_exclude_gc_and_release_across_transactions(storage):
    _, engine, _ = storage
    with MaintenanceGuard(engine) as first:
        first.commit()
        with MaintenanceGuard(engine) as second:
            first.check()
            second.check()

            def attempt_gc():
                with pytest.raises(MaintenanceBusy):
                    with MaintenanceGuard(engine, exclusive=True):
                        pass

            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(attempt_gc).result(timeout=5)
    with MaintenanceGuard(engine, exclusive=True) as gc:
        gc.check(exclusive=True)
        with pytest.raises(MaintenanceBusy):
            with MaintenanceGuard(engine):
                pass
    with MaintenanceGuard(engine) as released:
        released.check()


def test_failed_metadata_commit_leaves_only_collectable_orphan(storage):
    local, engine, root = storage
    with engine.begin() as db:
        db.execute(
            text(
                "CREATE TABLE test_metadata (key uuid PRIMARY KEY, parent uuid REFERENCES test_metadata(key) DEFERRABLE INITIALLY DEFERRED)"
            )
        )
    with pytest.raises(StorageUnavailable):
        with MaintenanceGuard(engine) as lease:
            blob = local.publish(io.BytesIO(b"metadata rollback"), lease)
            pid = lease.connection.scalar(text("SELECT pg_backend_pid()"))
            lease.connection.execute(
                text("INSERT INTO test_metadata VALUES (:key,:parent)"),
                {"key": blob.key.id, "parent": uuid4()},
            )
            lease.commit()
    with engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM test_metadata")) == 0
    await_backend_exit(engine, pid)
    age(root / "revisions" / str(blob.key.id))
    with MaintenanceGuard(engine, exclusive=True) as lease:
        assert local.delete(blob.key, lease, References())


def test_lost_connection_stops_publication_and_cannot_reconnect_commit(storage):
    local, engine, root = storage
    with MaintenanceGuard(engine) as lease:
        pid = lease.connection.scalar(text("SELECT pg_backend_pid()"))
        with engine.begin() as killer:
            killer.execute(text("SELECT pg_terminate_backend(:pid)"), {"pid": pid})
        for action in [
            lambda: local.publish(io.BytesIO(b"lost"), lease),
            lease.commit,
            lease.check,
        ]:
            with pytest.raises(StorageUnavailable):
                action()
    assert list((root / "revisions").iterdir()) == []
    with MaintenanceGuard(engine, exclusive=True) as next_owner:
        next_owner.check(exclusive=True)


def test_directory_replacement_between_check_and_rename_is_confined(storage, monkeypatch):
    from forma_backend.infrastructure.storage import local as module

    local, engine, root = storage
    outside = root / "outside"
    outside.mkdir()
    original = os.rename

    def swapped(source, destination, **kwargs):
        original(root / "revisions", root / "detached")
        (root / "revisions").symlink_to(outside, target_is_directory=True)
        return original(source, destination, **kwargs)

    with MaintenanceGuard(engine) as lease, monkeypatch.context() as patched:
        patched.setattr(module.os, "rename", swapped)
        with pytest.raises(StorageUnavailable):
            local.publish(io.BytesIO(b"confined orphan"), lease)
    assert list(outside.iterdir()) == []
    assert list((root / "temp").iterdir()) == []
    assert len(list((root / "detached").iterdir())) == 1


def test_post_rename_failure_leaves_fresh_unreferenced_orphan(storage, monkeypatch):
    from forma_backend.infrastructure.storage import local as module

    local, engine, root = storage
    original = os.fsync
    calls = 0

    def fail_directory(fd):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError(errno.EIO, "fsync directory failed")
        return original(fd)

    with MaintenanceGuard(engine) as lease, monkeypatch.context() as patched:
        patched.setattr(module.os, "fsync", fail_directory)
        with pytest.raises(StorageUnavailable):
            local.publish(io.BytesIO(b"orphan after rename"), lease)
    (path,) = (root / "revisions").iterdir()
    key = BlobKey(BlobArea.REVISIONS, UUID(path.name))
    with MaintenanceGuard(engine, exclusive=True) as lease:
        assert not local.delete(key, lease, References())
        age(path)
        assert local.delete(key, lease, References())


def test_connection_loss_while_streaming_prevents_rename(storage):
    local, engine, root = storage
    with MaintenanceGuard(engine) as lease:
        pid = lease.connection.scalar(text("SELECT pg_backend_pid()"))

        class BrokenStream(io.BytesIO):
            killed = False

            def read(self, size=-1):
                if not self.killed:
                    self.killed = True
                    with engine.begin() as killer:
                        killer.execute(text("SELECT pg_terminate_backend(:pid)"), {"pid": pid})
                return super().read(size)

        with pytest.raises(StorageUnavailable):
            local.publish(BrokenStream(b"uncommitted streaming"), lease)
        with pytest.raises(StorageUnavailable):
            lease.commit()
    assert list((root / "revisions").iterdir()) == []
    assert list((root / "temp").iterdir()) == []


def test_explicit_unlock_is_detected_and_pool_does_not_leak_guard(storage):
    _, engine, _ = storage
    from forma_backend.infrastructure.storage.maintenance import NAMESPACE, LOCK_ID

    with MaintenanceGuard(engine) as lease:
        lease.connection.execute(
            text("SELECT pg_advisory_unlock_shared(:ns,:id)"), {"ns": NAMESPACE, "id": LOCK_ID}
        )
        with pytest.raises(StorageUnavailable):
            lease.commit()
        with pytest.raises(StorageUnavailable):
            lease.connection
    with MaintenanceGuard(engine, exclusive=True) as gc:
        gc.check(exclusive=True)
    for _ in range(3):
        with MaintenanceGuard(engine) as reader:
            reader.check()
    with MaintenanceGuard(engine, exclusive=True):
        pass


@pytest.mark.parametrize("replacement", ["root-symlink", "parent-symlink", "writable-root"])
def test_untrusted_layout_is_rejected_at_initialization(tmp_path, replacement):
    actual = tmp_path / "actual"
    actual.mkdir()
    alias = tmp_path / "alias"
    if replacement == "root-symlink":
        alias.symlink_to(actual, target_is_directory=True)
        root = alias
    elif replacement == "parent-symlink":
        (actual / "nested").mkdir()
        alias.symlink_to(actual, target_is_directory=True)
        root = alias / "nested"
    else:
        os.chmod(actual, 0o777)
        root = actual
    with pytest.raises(StorageUnavailable):
        LocalFileStorage(root)


def test_file_swap_after_open_never_reads_symlink_target(storage, monkeypatch):
    from forma_backend.infrastructure.storage import local as module

    local, engine, root = storage
    with MaintenanceGuard(engine) as lease:
        blob = local.publish(io.BytesIO(b"inside"), lease)
        path = root / "revisions" / str(blob.key.id)
        outside = root / "outside-file"
        outside.write_bytes(b"secret outside sentinel")
        original = os.open

        def swapped(name, flags, *args, **kwargs):
            fd = original(name, flags, *args, **kwargs)
            if name == str(blob.key.id) and flags & os.O_NONBLOCK:
                path.unlink()
                path.symlink_to(outside)
            return fd

        with monkeypatch.context() as patched:
            patched.setattr(module.os, "open", swapped)
            with pytest.raises(StorageUnavailable):
                local.open(blob.key, lease)
        assert outside.read_bytes() == b"secret outside sentinel"


def test_guarded_metadata_commit_and_authoritative_gc_probe(storage):
    local, engine, root = storage
    with engine.begin() as db:
        db.execute(text("CREATE TABLE test_blob_refs (key uuid PRIMARY KEY)"))
    with MaintenanceGuard(engine) as lease:
        blob = local.publish(io.BytesIO(b"committed metadata"), lease)
        lease.connection.execute(
            text("INSERT INTO test_blob_refs VALUES (:key)"), {"key": blob.key.id}
        )
        with engine.connect() as reader:
            assert reader.scalar(text("SELECT count(*) FROM test_blob_refs")) == 0
        lease.commit()
        with engine.connect() as reader:
            assert reader.scalar(text("SELECT count(*) FROM test_blob_refs")) == 1
    age(root / "revisions" / str(blob.key.id))
    with MaintenanceGuard(engine, exclusive=True) as gc:

        class DatabaseReferences:
            def is_referenced(self, key):
                return gc.connection.scalar(
                    text("SELECT EXISTS(SELECT 1 FROM test_blob_refs WHERE key=:key)"),
                    {"key": key.id},
                )

        assert not local.delete(blob.key, gc, DatabaseReferences())
        gc.connection.execute(text("DELETE FROM test_blob_refs"))
        gc.commit()
        assert local.delete(blob.key, gc, DatabaseReferences())


def test_early_connection_close_does_not_return_a_locked_session_to_pool(storage):
    _, engine, _ = storage
    with MaintenanceGuard(engine) as lease:
        pid = lease.connection.scalar(text("SELECT pg_backend_pid()"))
        lease.connection.close()
        with pytest.raises(StorageUnavailable):
            lease.commit()
    await_backend_exit(engine, pid)
    with MaintenanceGuard(engine, exclusive=True) as gc:
        gc.check(exclusive=True)


def test_gc_requires_a_definite_reference_answer(storage):
    local, engine, root = storage
    with MaintenanceGuard(engine) as lease:
        blob = local.publish(io.BytesIO(b"unknown reference state"), lease)
    age(root / "revisions" / str(blob.key.id))

    class Unknown:
        def is_referenced(self, key):
            return None

    with MaintenanceGuard(engine, exclusive=True) as gc:
        with pytest.raises(StorageUnavailable):
            local.delete(blob.key, gc, Unknown())
        with local.open(blob.key, gc) as handle:
            assert handle.read() == b"unknown reference state"


def test_detached_guard_connections_are_bounded_and_slots_released(storage):
    from contextlib import ExitStack

    _, engine, _ = storage
    with ExitStack() as stack:
        for _ in range(8):
            stack.enter_context(MaintenanceGuard(engine))
        with pytest.raises(MaintenanceBusy):
            with MaintenanceGuard(engine):
                pass
    with MaintenanceGuard(engine, exclusive=True) as gc:
        gc.check(exclusive=True)


def test_root_replacement_during_streaming_is_detected(storage):
    local, engine, root = storage
    detached = root.parent / (root.name + "-detached")
    outside = root.parent / (root.name + "-outside")
    outside.mkdir()

    class ReplacedRoot(io.BytesIO):
        replaced = False

        def read(self, size=-1):
            if not self.replaced:
                self.replaced = True
                root.rename(detached)
                root.symlink_to(outside, target_is_directory=True)
            return super().read(size)

    try:
        with MaintenanceGuard(engine) as lease:
            with pytest.raises(StorageUnavailable):
                local.publish(ReplacedRoot(b"detached staging"), lease)
        assert list(outside.iterdir()) == []
        assert list((detached / "temp").iterdir()) == []
        assert list((detached / "revisions").iterdir()) == []
    finally:
        if root.is_symlink():
            root.unlink()
            detached.rename(root)


def test_production_capacity_floors_admit_sufficient_space(storage, monkeypatch):
    from forma_backend.infrastructure.storage import local as module
    from types import SimpleNamespace

    _, engine, root = storage
    local = LocalFileStorage(root)
    fake = SimpleNamespace(f_bavail=3 * 1024**3, f_blocks=20 * 1024**3, f_frsize=1)
    with MaintenanceGuard(engine) as lease, monkeypatch.context() as patched:
        patched.setattr(module.os, "fstatvfs", lambda fd: fake)
        blob = local.publish(io.BytesIO(b"capacity admitted"), lease)
        with local.open(blob.key, lease) as handle:
            assert handle.read() == b"capacity admitted"


def test_gc_does_not_unlink_unsafe_entries(storage):
    local, engine, root = storage
    outside = root / "outside-gc-sentinel"
    outside.write_bytes(b"keep sentinel")
    old = root / "revisions" / str(uuid4())
    old.symlink_to(outside)
    temporary = root / "temp" / str(uuid4())
    temporary.symlink_to(outside)
    with MaintenanceGuard(engine, exclusive=True) as gc:
        with pytest.raises(StorageUnavailable):
            local.delete(BlobKey(BlobArea.REVISIONS, UUID(old.name)), gc, References())
        with pytest.raises(StorageUnavailable):
            local.collect_temp(gc)
    assert old.is_symlink() and temporary.is_symlink()
    assert outside.read_bytes() == b"keep sentinel"


def test_process_crash_after_publish_rolls_back_metadata_and_keeps_orphan(storage, database_url):
    import json
    import select
    import subprocess
    import sys

    local, engine, root = storage
    with engine.begin() as db:
        db.execute(text("CREATE TABLE test_crash_refs (key uuid PRIMARY KEY)"))
    program = """
import io,json,os,sys
from pathlib import Path
from sqlalchemy import text
from forma_backend.infrastructure.database.session import create_database_engine
from forma_backend.infrastructure.storage.local import LocalFileStorage
from forma_backend.infrastructure.storage.maintenance import MaintenanceGuard
engine=create_database_engine(os.environ['DATABASE_URL'])
storage=LocalFileStorage(Path(os.environ['STORAGE_ROOT']),min_free_bytes=0,min_free_ratio=0)
with MaintenanceGuard(engine) as lease:
    blob=storage.publish(io.BytesIO(b'killed before metadata commit'),lease)
    lease.connection.execute(text('INSERT INTO test_crash_refs VALUES (:key)'),{'key':blob.key.id})
    pid=lease.connection.scalar(text('SELECT pg_backend_pid()'))
    print(json.dumps({'key':str(blob.key.id),'pid':pid}),flush=True)
    sys.stdin.readline()
"""
    process = subprocess.Popen(
        [sys.executable, "-c", program],
        env={
            "DATABASE_URL": database_url.render_as_string(hide_password=False),
            "STORAGE_ROOT": str(root),
        },
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert select.select([process.stdout], [], [], 10)[0], (
            "Publisher did not reach commit boundary"
        )
        marker = json.loads(process.stdout.readline())
        assert process.poll() is None
        process.kill()
        assert process.wait(timeout=5) == -9
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        for pipe in [process.stdin, process.stdout, process.stderr]:
            pipe.close()
    await_backend_exit(engine, marker["pid"])
    with engine.connect() as db:
        assert db.scalar(text("SELECT count(*) FROM test_crash_refs")) == 0
    key = BlobKey(BlobArea.REVISIONS, UUID(marker["key"]))
    with MaintenanceGuard(engine, exclusive=True) as gc:
        with local.open(key, gc) as handle:
            assert handle.read() == b"killed before metadata commit"
        assert not local.delete(key, gc, References())
        age(root / "revisions" / str(key.id))
        assert local.delete(key, gc, References())
