"""Real PostgreSQL project ACL, revision serialization and retention tests."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import text

from test_sessions import setup_client, login

ROOT = "/api/v1/projects"


@pytest.fixture
def world(database_url, tmp_path):
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            actors = {}
            for name in ["owner", "editor", "viewer", "stranger"]:
                email = name + "@example.org"
                if name != "owner":
                    assert (
                        client.post(
                            "/api/v1/auth/register",
                            json={
                                "email": email,
                                "password": "correct horse battery",
                                "display_name": name,
                            },
                        ).status_code
                        == 201
                    )
                token = login(client, email)
                actors[name] = {"Authorization": "Bearer " + token["access_token"]}
            response = client.post(
                ROOT,
                headers=actors["owner"],
                json={"title": "Shared paper", "description": "Scientific content"},
            )
            assert response.status_code == 201
            project = response.json()
            with engine.begin() as db:
                for name in ["editor", "viewer"]:
                    db.execute(
                        text(
                            "INSERT INTO project_members(project_id,user_id,role,invited_by) SELECT :project,id,:role,:owner FROM users WHERE email=:email"
                        ),
                        {
                            "project": project["id"],
                            "owner": project["owner_id"],
                            "role": name,
                            "email": name + "@example.org",
                        },
                    )
            yield client, engine, actors, project
    finally:
        engine.dispose()


def patch(client, identifier, actor, revision=1, title="Changed paper"):
    return client.patch(
        ROOT + "/" + identifier,
        headers=actor,
        json={"title": title, "description": "Updated", "expected_revision": revision},
    )


def remove(client, project, actor, revision=1, title=None):
    return client.request(
        "DELETE",
        ROOT + "/" + project["id"],
        headers=actor,
        json={
            "confirm_title": title if title is not None else project["title"],
            "expected_revision": revision,
        },
    )


def test_acl_read_list_and_writer_matrix(world):
    client, _, actors, project = world
    path = ROOT + "/" + project["id"]
    assert client.get(path).status_code == 401
    for name in ["owner", "editor", "viewer"]:
        response = client.get(path, headers=actors[name])
        assert response.status_code == 200, response.text
        assert response.json()["role"] == name
        listing = client.get(ROOT, headers=actors[name])
        assert listing.status_code == 200 and listing.json()["items"][0]["id"] == project["id"]
    assert client.get(path, headers=actors["stranger"]).status_code == 404
    assert client.get(ROOT, headers=actors["stranger"]).json()["items"] == []
    assert patch(client, project["id"], actors["viewer"]).status_code == 403
    assert patch(client, project["id"], actors["stranger"]).status_code == 404
    changed = patch(client, project["id"], actors["editor"])
    assert (
        changed.status_code == 200
        and changed.json()["revision"] == 2
        and changed.json()["role"] == "editor"
    )
    stale = patch(client, project["id"], actors["owner"])
    assert stale.status_code == 409 and stale.json()["error"]["code"] == "REVISION_CONFLICT"
    assert stale.json()["error"]["details"]["current_revision"] == 2


def test_delete_restore_visibility_revision_and_confirm(world):
    client, _, actors, project = world
    path = ROOT + "/" + project["id"]
    for name in ["editor", "viewer"]:
        assert remove(client, project, actors[name]).status_code == 403
    assert remove(client, project, actors["stranger"]).status_code == 404
    assert remove(client, project, actors["owner"], title="Wrong").status_code == 409
    assert client.get(path, headers=actors["owner"]).json()["revision"] == 1
    deleted = remove(client, project, actors["owner"])
    assert deleted.status_code == 204 and not deleted.content
    own = client.get(path, headers=actors["owner"]).json()
    assert own["status"] == "deleted" and own["revision"] == 2 and own["deleted_at"] is not None
    assert client.get(ROOT, headers=actors["owner"]).json()["items"] == []
    assert (
        client.get(ROOT + "?status=deleted", headers=actors["owner"]).json()["items"][0]["id"]
        == project["id"]
    )
    for name in ["editor", "viewer", "stranger"]:
        assert client.get(path, headers=actors[name]).status_code == 404
        assert client.get(ROOT + "?status=deleted", headers=actors[name]).json()["items"] == []
        assert (
            client.post(
                path + "/restore", headers=actors[name], json={"expected_revision": 2}
            ).status_code
            == 404
        )
    assert patch(client, project["id"], actors["owner"], 2).status_code == 404
    assert (
        client.post(
            path + "/restore", headers=actors["owner"], json={"expected_revision": 1}
        ).status_code
        == 409
    )
    restored = client.post(
        path + "/restore", headers=actors["owner"], json={"expected_revision": 2}
    )
    assert restored.status_code == 200 and restored.json()["revision"] == 3
    assert restored.json()["deleted_at"] is None and restored.json()["status"] == "active"
    assert (
        client.post(
            path + "/restore", headers=actors["owner"], json={"expected_revision": 3}
        ).status_code
        == 409
    )
    assert remove(client, project, actors["owner"], revision=1).status_code == 409


def test_expired_restore_keeps_deleted_metadata(world):
    client, engine, actors, project = world
    assert remove(client, project, actors["owner"]).status_code == 204
    with engine.begin() as db:
        db.execute(
            text("UPDATE projects SET deleted_at=clock_timestamp()-interval '8 days' WHERE id=:id"),
            {"id": project["id"]},
        )
    response = client.post(
        ROOT + "/" + project["id"] + "/restore",
        headers=actors["owner"],
        json={"expected_revision": 2},
    )
    assert response.status_code == 410 and response.json()["error"]["code"] == "RETENTION_EXPIRED"
    with engine.connect() as db:
        assert db.execute(
            text("SELECT status,revision FROM projects WHERE id=:id"), {"id": project["id"]}
        ).one() == ("deleted", 2)


def test_list_search_keyset_and_cursor_filter_binding(world):
    client, _, actors, project = world
    for title in ["Alpha 100%", "ALPHA second", "literal_underscore", "Unrelated"]:
        assert client.post(ROOT, headers=actors["owner"], json={"title": title}).status_code == 201
    matches = client.get(ROOT, params={"q": "alpha", "limit": 1}, headers=actors["owner"])
    assert matches.status_code == 200
    first = matches.json()
    second = client.get(
        ROOT,
        params={"q": "alpha", "limit": 1, "cursor": first["next_cursor"]},
        headers=actors["owner"],
    ).json()
    assert len(second["items"]) == 1 and second["next_cursor"] is None
    assert first["items"][0]["id"] != second["items"][0]["id"]
    for params, actor in [
        ({"q": "different", "cursor": first["next_cursor"]}, "owner"),
        ({"q": "alpha", "cursor": first["next_cursor"]}, "editor"),
        ({"q": "alpha", "status": "deleted", "cursor": first["next_cursor"]}, "owner"),
        ({"cursor": "invalid"}, "owner"),
    ]:
        response = client.get(ROOT, params=params, headers=actors[actor])
        assert response.status_code == 400 and response.json()["error"]["code"] == "INVALID_CURSOR"
    assert len(client.get(ROOT, params={"q": "%"}, headers=actors["owner"]).json()["items"]) == 1
    assert len(client.get(ROOT, params={"q": "_"}, headers=actors["owner"]).json()["items"]) == 1
    assert (
        client.get(ROOT, params={"q": "scientific"}, headers=actors["editor"]).json()["items"][0][
            "id"
        ]
        == project["id"]
    )
    for params in [
        {"limit": 0},
        {"limit": 101},
        {"status": "unknown"},
        {"q": "x" * 201},
        {"q": "bad\x00query"},
    ]:
        assert client.get(ROOT, params=params, headers=actors["owner"]).status_code == 422


def test_concurrent_writers_get_one_revision_conflict(world, monkeypatch):
    from forma_backend.infrastructure.projects.crud_store import SqlProjectCrudStore

    client, _, actors, project = world
    arrived = Barrier(2)
    original = SqlProjectCrudStore.access_context

    def synchronized(self, identifier, actor_id):
        value = original(self, identifier, actor_id)
        arrived.wait(timeout=10)
        return value

    monkeypatch.setattr(SqlProjectCrudStore, "access_context", synchronized)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(lambda name: patch(client, project["id"], actors[name]), ["owner", "editor"])
        )
    assert sorted(r.status_code for r in responses) == [200, 409]
    assert client.get(ROOT + "/" + project["id"], headers=actors["owner"]).json()["revision"] == 2


def test_mutation_rollback_when_guard_commit_fails(world, monkeypatch):
    from forma_backend.infrastructure.storage.maintenance import MaintenanceGuard
    from forma_backend.modules.project_files.storage import StorageUnavailable

    client, _, actors, project = world

    def failed(self):
        raise StorageUnavailable()

    monkeypatch.setattr(MaintenanceGuard, "commit", failed)
    assert patch(client, project["id"], actors["editor"]).status_code == 503
    unchanged = client.get(ROOT + "/" + project["id"], headers=actors["owner"]).json()
    assert unchanged["revision"] == 1 and unchanged["title"] == project["title"]


def test_missing_and_foreign_ids_share_error_and_input_validation(world):
    import json

    client, _, actors, project = world
    for identifier in [project["id"], str(uuid4())]:
        response = client.get(ROOT + "/" + identifier, headers=actors["stranger"])
        assert response.status_code == 404 and response.json()["error"]["code"] == "NOT_FOUND"
    path = ROOT + "/" + project["id"]
    for extra in [{"owner_id": str(uuid4())}, {"role": "owner"}, {"main_file_id": str(uuid4())}]:
        payload = {"title": "Valid", "description": "", "expected_revision": 1, **extra}
        assert client.patch(path, headers=actors["owner"], json=payload).status_code == 422
    for title in [" ", "bad\x00title", "bad\ud800title"]:
        response = client.patch(
            path,
            headers={**actors["owner"], "Content-Type": "application/json"},
            content=json.dumps({"title": title, "description": "", "expected_revision": 1}),
        )
        assert response.status_code == 422


@pytest.mark.parametrize("isolation", ["READ COMMITTED", "REPEATABLE READ"])
def test_cross_owned_edits_use_sorted_locks_without_deadlock(world, monkeypatch, isolation):
    from forma_backend.infrastructure.projects.crud_store import SqlProjectCrudStore

    client, engine, actors, first = world
    second = client.post(ROOT, headers=actors["editor"], json={"title": "Editor owned"}).json()
    with engine.begin() as db:
        db.execute(
            text(
                "INSERT INTO project_members(project_id,user_id,role,invited_by) VALUES (:project,:member,'editor',:owner)"
            ),
            {"project": second["id"], "member": first["owner_id"], "owner": second["owner_id"]},
        )
    engine.update_execution_options(isolation_level=isolation)
    arrived = Barrier(2)
    original = SqlProjectCrudStore.access_context

    def synchronized(self, identifier, actor_id):
        value = original(self, identifier, actor_id)
        arrived.wait(timeout=10)
        return value

    monkeypatch.setattr(SqlProjectCrudStore, "access_context", synchronized)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda item: patch(client, item[0], actors[item[1]]),
                [(first["id"], "editor"), (second["id"], "owner")],
            )
        )
    assert [r.status_code for r in responses] == [200, 200]
    assert all(r.json()["role"] == "editor" and r.json()["revision"] == 2 for r in responses)


def test_membership_revoked_while_waiting_project_lock_is_rechecked(world, monkeypatch):
    from threading import Event
    from forma_backend.infrastructure.projects.crud_store import SqlProjectCrudStore

    client, engine, actors, project = world
    waiting = Event()
    original = SqlProjectCrudStore.load

    def observed(self, identifier, actor_id, *, lock=False):
        if lock:
            waiting.set()
        return original(self, identifier, actor_id, lock=lock)

    monkeypatch.setattr(SqlProjectCrudStore, "load", observed)
    with ThreadPoolExecutor(max_workers=1) as pool:
        with engine.begin() as blocker:
            blocker.execute(
                text("SELECT id FROM projects WHERE id=:id FOR UPDATE"), {"id": project["id"]}
            )
            pending = pool.submit(patch, client, project["id"], actors["editor"])
            assert waiting.wait(5)
            blocker.execute(
                text("DELETE FROM project_members WHERE project_id=:id AND role='editor'"),
                {"id": project["id"]},
            )
        response = pending.result(timeout=6)
    assert response.status_code == 404
    assert client.get(ROOT + "/" + project["id"], headers=actors["owner"]).json()["revision"] == 1


def test_revoked_actor_after_initial_auth_cannot_mutate(world, monkeypatch):
    from threading import Event
    from forma_backend.infrastructure.projects.crud_store import SqlProjectCrudStore

    client, engine, actors, project = world
    arrived, release = Event(), Event()
    original = SqlProjectCrudStore.access_context

    def delayed(self, identifier, actor_id):
        value = original(self, identifier, actor_id)
        arrived.set()
        assert release.wait(10)
        return value

    monkeypatch.setattr(SqlProjectCrudStore, "access_context", delayed)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(patch, client, project["id"], actors["editor"])
        try:
            assert arrived.wait(5)
            with engine.begin() as db:
                db.execute(
                    text(
                        "UPDATE auth_sessions SET revoked_at=clock_timestamp() WHERE user_id=(SELECT id FROM users WHERE email='editor@example.org')"
                    )
                )
        finally:
            release.set()
        assert pending.result(timeout=6).status_code == 401
    assert client.get(ROOT + "/" + project["id"], headers=actors["owner"]).json()["revision"] == 1


def test_list_projection_has_no_per_project_queries(world):
    from sqlalchemy import event

    client, engine, actors, _ = world
    for n in range(5):
        assert (
            client.post(ROOT, headers=actors["owner"], json={"title": f"Extra {n}"}).status_code
            == 201
        )
    queries = []

    def record(conn, cursor, statement, parameters, context, many):
        if "FROM projects" in statement:
            queries.append(statement)

    event.listen(engine, "before_cursor_execute", record)
    try:
        response = client.get(ROOT, headers=actors["owner"])
    finally:
        event.remove(engine, "before_cursor_execute", record)
    assert response.status_code == 200 and len(response.json()["items"]) == 6
    assert len(queries) == 1


def test_soft_delete_does_not_release_retained_quota(world):
    client, engine, actors, project = world
    with engine.begin() as db:
        db.execute(
            text(
                "INSERT INTO projects(id,owner_id,title) SELECT gen_random_uuid(),:owner,'Retained' FROM generate_series(1,99)"
            ),
            {"owner": project["owner_id"]},
        )
    assert remove(client, project, actors["owner"]).status_code == 204
    assert (
        client.post(ROOT, headers=actors["owner"], json={"title": "Still full"}).status_code == 429
    )
    assert (
        client.post(
            ROOT + "/" + project["id"] + "/restore",
            headers=actors["owner"],
            json={"expected_revision": 2},
        ).status_code
        == 200
    )


@pytest.mark.parametrize("actor,status", [("stranger", 404), ("viewer", 403)])
def test_denied_mutation_does_not_wait_on_owner_lock(world, actor, status):
    client, engine, actors, project = world
    with engine.begin() as blocker:
        blocker.execute(
            text("SELECT id FROM users WHERE id=:owner FOR UPDATE"), {"owner": project["owner_id"]}
        )
        response = patch(client, project["id"], actors[actor])
        assert response.status_code == status
