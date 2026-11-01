from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from forma_backend.modules.access.policy import ProjectAccessContext
from forma_backend.modules.identity.sessions import Principal
from forma_backend.modules.projects.application import ProjectRecord, ProjectFailure
from forma_backend.modules.projects.crud import ProjectCrud, ProjectState


@pytest.mark.parametrize("extra", [timedelta(0), timedelta(microseconds=1)])
def test_exact_seven_day_restore_boundary(extra):
    now = datetime(2026, 11, 1, tzinfo=UTC)
    actor = Principal(uuid4(), uuid4())
    identifier = uuid4()
    record = ProjectRecord(
        identifier,
        actor.user_id,
        "Paper",
        "",
        2,
        "deleted",
        now - timedelta(days=10),
        now - timedelta(days=7) - extra,
        now - timedelta(days=7) - extra,
    )
    work = MagicMock()
    work.__enter__.return_value = work
    work.access_context.return_value = ProjectAccessContext(identifier, actor.user_id, deleted=True)
    work.authenticate.return_value = True
    work.load.return_value = ProjectState(
        record, ProjectAccessContext(identifier, actor.user_id, deleted=True)
    )
    work.now.return_value = now
    service = ProjectCrud(lambda: work)
    if extra:
        with pytest.raises(ProjectFailure) as failure:
            service.restore(actor, identifier, 2)
        assert failure.value.code == "RETENTION_EXPIRED"
        work.commit.assert_not_called()
        work.save.assert_not_called()
    else:
        restored = service.restore(actor, identifier, 2)
        assert restored.record.status == "active" and restored.record.revision == 3
        work.commit.assert_called_once()
