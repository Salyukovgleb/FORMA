"""Executed inside the disposable Compose image before/after recreation; no production data."""

import io
from pathlib import Path
from uuid import UUID

from forma_backend.core.config import load_settings
from forma_backend.infrastructure.database.session import create_database_engine
from forma_backend.infrastructure.storage.local import LocalFileStorage
from forma_backend.infrastructure.storage.maintenance import MaintenanceGuard
from forma_backend.modules.project_files.storage import BlobKey, BlobArea


def main() -> None:
    settings = load_settings()
    engine = create_database_engine(settings.database_url.get_secret_value())
    # Capacity has dedicated floor/ratio tests; this smoke checks packaged I/O and persistence.
    storage = LocalFileStorage(Path("/var/lib/forma"), min_free_bytes=0, min_free_ratio=0)
    marker = Path("/var/lib/forma/blob-smoke-id")
    try:
        with MaintenanceGuard(engine) as guard:
            if marker.exists():
                key = BlobKey(BlobArea.REVISIONS, UUID(marker.read_text()))
            else:
                blob = storage.publish(io.BytesIO(b"persisted immutable blob"), guard)
                key = blob.key
                marker.write_text(str(key.id))
            with storage.open(key, guard) as handle:
                assert handle.read() == b"persisted immutable blob"
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
