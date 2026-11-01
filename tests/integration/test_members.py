from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from test_project_crud import world as project_world

world = project_world


def test_member_acl_lifecycle(world):
    client, engine, actors, project = world
    path = "/api/v1/projects/" + project["id"] + "/members"
    assert client.get(path, headers=actors["stranger"]).status_code == 404
    members = client.get(path, headers=actors["viewer"])
    assert members.status_code == 200 and len(members.json()["items"]) == 3
    assert (
        client.post(
            path, headers=actors["owner"], json={"email": "bad\u0000@example.org", "role": "viewer"}
        ).status_code
        == 422
    )
    owner = project["owner_id"]
    assert client.delete(path + "/" + owner, headers=actors["owner"]).status_code == 409
    assert (
        client.patch(
            path + "/" + owner, headers=actors["owner"], json={"role": "viewer"}
        ).status_code
        == 409
    )
    payload = {"email": "stranger@example.org", "role": "editor"}
    assert client.post(path, headers=actors["editor"], json=payload).status_code == 403
    added = client.post(path, headers=actors["owner"], json=payload)
    assert added.status_code == 201
    identifier = added.json()["user_id"]
    assert client.delete(path + "/" + identifier, headers=actors["viewer"]).status_code == 403
    assert client.post(path, headers=actors["owner"], json=payload).status_code == 409
    assert (
        client.patch(
            path + "/" + identifier, headers=actors["owner"], json={"role": "viewer"}
        ).json()["role"]
        == "viewer"
    )
    assert (
        client.patch(
            path + "/" + identifier, headers=actors["stranger"], json={"role": "editor"}
        ).status_code
        == 403
    )
    assert client.delete(path + "/" + identifier, headers=actors["stranger"]).status_code == 204
    assert client.delete(path + "/" + identifier, headers=actors["stranger"]).status_code == 404
    assert (
        client.post(
            path, headers=actors["owner"], json={"email": "absent@example.org", "role": "editor"}
        ).status_code
        == 404
    )
    assert (
        client.post(
            path, headers=actors["owner"], json={"email": "owner@example.org", "role": "viewer"}
        ).status_code
        == 409
    )
    assert (
        client.post(
            path, headers=actors["owner"], json={"email": "stranger@example.org", "role": "owner"}
        ).status_code
        == 422
    )
    assert (
        client.patch(
            path + "/" + str(uuid4()), headers=actors["owner"], json={"role": "editor"}
        ).status_code
        == 404
    )
    assert (
        client.get("/api/v1/projects/" + project["id"], headers=actors["owner"]).json()["revision"]
        == 1
    )

    editor = next(
        m
        for m in client.get(path, headers=actors["owner"]).json()["items"]
        if m["role"] == "editor"
    )["user_id"]
    assert client.delete(path + "/" + editor, headers=actors["owner"]).status_code == 204
    assert client.get(path, headers=actors["editor"]).status_code == 404


def test_concurrent_grants_are_serialized(world, monkeypatch):
    from threading import Barrier
    from forma_backend.infrastructure.projects.members import SqlMemberStore

    arrived = Barrier(2)
    original = SqlMemberStore.access_context

    def synchronized(self, identifier, actor_id):
        result = original(self, identifier, actor_id)
        arrived.wait(timeout=10)
        return result

    monkeypatch.setattr(SqlMemberStore, "access_context", synchronized)
    client, _, actors, project = world
    path = "/api/v1/projects/" + project["id"] + "/members"
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda _: client.post(
                    path,
                    headers=actors["owner"],
                    json={"email": "stranger@example.org", "role": "viewer"},
                ).status_code,
                range(2),
            )
        )
    assert sorted(results) == [201, 409]


def test_deleted_members_hidden_and_commit_rollback(world, monkeypatch):
    from forma_backend.infrastructure.storage.maintenance import MaintenanceGuard

    client, engine, actors, project = world
    path = "/api/v1/projects/" + project["id"] + "/members"
    original = MaintenanceGuard.commit

    def failed(self):
        from forma_backend.modules.project_files.storage import StorageUnavailable

        raise StorageUnavailable()

    monkeypatch.setattr(MaintenanceGuard, "commit", failed)
    response = client.post(
        path, headers=actors["owner"], json={"email": "stranger@example.org", "role": "viewer"}
    )
    assert response.status_code == 503
    monkeypatch.setattr(MaintenanceGuard, "commit", original)
    assert len(client.get(path, headers=actors["owner"]).json()["items"]) == 3
    assert (
        client.request(
            "DELETE",
            "/api/v1/projects/" + project["id"],
            headers=actors["owner"],
            json={"expected_revision": 1, "confirm_title": project["title"]},
        ).status_code
        == 204
    )
    assert client.get(path, headers=actors["owner"]).status_code == 404


def test_member_limit_includes_owner_and_does_not_partially_grant(world):
    from sqlalchemy import text

    client, engine, actors, project = world
    with engine.begin() as db:
        db.execute(
            text(
                "INSERT INTO users(id,email,password_hash,display_name) SELECT gen_random_uuid(),'member'||n||'@example.org','not-a-login-hash','Fixture' FROM generate_series(1,47) n"
            )
        )
        db.execute(
            text(
                "INSERT INTO project_members(project_id,user_id,role,invited_by) SELECT :p,id,'viewer',:o FROM users WHERE email LIKE 'member%@example.org'"
            ),
            {"p": project["id"], "o": project["owner_id"]},
        )
    path = "/api/v1/projects/" + project["id"] + "/members"
    assert len(client.get(path, headers=actors["owner"]).json()["items"]) == 50
    assert (
        client.post(
            path, headers=actors["owner"], json={"email": "stranger@example.org", "role": "viewer"}
        ).status_code
        == 429
    )
    assert len(client.get(path, headers=actors["owner"]).json()["items"]) == 50


def test_members_recheck_acl_after_lock_wait(world, monkeypatch):
    from threading import Event
    from forma_backend.infrastructure.projects.members import SqlMemberStore
    from sqlalchemy import text

    client, engine, actors, project = world
    path = "/api/v1/projects/" + project["id"] + "/members"
    member = next(
        m
        for m in client.get(path, headers=actors["owner"]).json()["items"]
        if m["role"] == "editor"
    )["user_id"]
    waiting = Event()
    original = SqlMemberStore.load

    def observed(self, identifier, actor_id, *, lock=False):
        if lock:
            waiting.set()
        return original(self, identifier, actor_id, lock=lock)

    monkeypatch.setattr(SqlMemberStore, "load", observed)
    with ThreadPoolExecutor(max_workers=1) as pool:
        with engine.begin() as db:
            db.execute(text("SELECT id FROM projects WHERE id=:p FOR UPDATE"), {"p": project["id"]})
            pending = pool.submit(client.delete, path + "/" + member, headers=actors["editor"])
            assert waiting.wait(5)
            db.execute(
                text("DELETE FROM project_members WHERE project_id=:p AND user_id=:u"),
                {"p": project["id"], "u": member},
            )
        assert pending.result(timeout=6).status_code == 404


def test_denied_member_grant_does_not_lock_foreign_owner(world):
    from sqlalchemy import text

    client, engine, actors, project = world
    path = "/api/v1/projects/" + project["id"] + "/members"
    with engine.begin() as db:
        db.execute(text("SELECT id FROM users WHERE id=:o FOR UPDATE"), {"o": project["owner_id"]})
        for actor, code in [("viewer", 403), ("stranger", 404)]:
            assert (
                client.post(
                    path,
                    headers=actors[actor],
                    json={"email": "stranger@example.org", "role": "editor"},
                ).status_code
                == code
            )


def test_revoked_session_cannot_commit_membership(world, monkeypatch):
    from threading import Event
    from sqlalchemy import text
    from forma_backend.infrastructure.projects.members import SqlMemberStore

    client, engine, actors, project = world
    path = "/api/v1/projects/" + project["id"] + "/members"
    reached, release = Event(), Event()
    original = SqlMemberStore.access_context

    def delayed(self, identifier, actor_id):
        result = original(self, identifier, actor_id)
        reached.set()
        assert release.wait(10)
        return result

    monkeypatch.setattr(SqlMemberStore, "access_context", delayed)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(
            client.post,
            path,
            headers=actors["owner"],
            json={"email": "stranger@example.org", "role": "viewer"},
        )
        try:
            assert reached.wait(5)
            with engine.begin() as db:
                db.execute(
                    text("UPDATE auth_sessions SET revoked_at=clock_timestamp() WHERE user_id=:o"),
                    {"o": project["owner_id"]},
                )
        finally:
            release.set()
        assert pending.result(timeout=6).status_code == 401
    with engine.connect() as db:
        assert (
            db.scalar(
                text("SELECT count(*) FROM project_members WHERE project_id=:p"),
                {"p": project["id"]},
            )
            == 2
        )
