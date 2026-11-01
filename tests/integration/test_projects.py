"""CreateProject owns its transaction, quota and authenticated owner identity."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from test_sessions import setup_client, login

PATH = "/api/v1/projects"


def authorization(client):
    return {"Authorization": "Bearer " + login(client)["access_token"]}


def seed_projects(engine, count):
    with engine.begin() as db:
        owner = db.scalar(text("SELECT id FROM users WHERE email='owner@example.org'"))
        db.execute(
            text(
                "INSERT INTO projects(id,owner_id,title) SELECT gen_random_uuid(),:owner,'Retained' FROM generate_series(1,:count)"
            ),
            {"owner": owner, "count": count},
        )
        db.execute(
            text(
                "UPDATE projects SET status='deleted',deleted_at=now() WHERE id=(SELECT id FROM projects LIMIT 1)"
            )
        )


def test_create_project_uses_current_owner_and_database_defaults(database_url, tmp_path):
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            assert client.post(PATH, json={"title": "Unauthenticated"}).status_code == 401
            headers = authorization(client)
            response = client.post(
                PATH, headers=headers, json={"title": "Статья", "description": "Описание"}
            )
            assert response.status_code == 201, response.text
            project = response.json()
            assert set(project) == {
                "id",
                "owner_id",
                "title",
                "description",
                "role",
                "status",
                "revision",
                "created_at",
                "updated_at",
                "deleted_at",
            }
            assert project["title"] == "Статья" and project["role"] == "owner"
            assert (
                project["revision"] == 1
                and project["status"] == "active"
                and project["deleted_at"] is None
            )
            UUID(project["id"])
            with engine.connect() as db:
                assert str(db.scalar(text("SELECT id FROM users"))) == project["owner_id"]
                row = db.execute(text("SELECT main_file_id,engine,description FROM projects")).one()
                assert tuple(row) == (None, "xelatex", "Описание")
                assert db.scalar(text("SELECT count(*) FROM project_members")) == 0
            assert client.get(PATH + "/" + project["id"], headers=headers).status_code == 404
    finally:
        engine.dispose()


def test_project_validation_and_unavailable_templates_leave_no_rows(database_url, tmp_path):
    import json

    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            headers = authorization(client)
            invalid = [
                {"title": " "},
                {"title": "\t\n"},
                {"title": "x" * 201},
                {"title": "bad\x00title"},
                {"title": "bad\ud800title"},
                {"title": "ok", "description": "bad\x00text"},
                {"title": "ok", "owner_id": str(uuid4())},
                {"title": "ok", "role": "owner"},
            ]
            for payload in invalid:
                response = client.post(
                    PATH,
                    content=json.dumps(payload),
                    headers={**headers, "Content-Type": "application/json"},
                )
                assert response.status_code == 422, response.text
            response = client.post(
                PATH, headers=headers, json={"title": "ok", "template_id": "unknown"}
            )
            assert response.status_code == 404 and response.json()["error"]["code"] == "NOT_FOUND"
            with engine.connect() as db:
                assert db.scalar(text("SELECT count(*) FROM projects")) == 0
    finally:
        engine.dispose()


@pytest.mark.parametrize("default_isolation", ["READ COMMITTED", "REPEATABLE READ"])
def test_concurrent_create_cannot_exceed_retained_owner_quota(
    database_url, tmp_path, monkeypatch, default_isolation
):
    from forma_backend.infrastructure.projects.persistence import SqlProjectUnitOfWork

    client, engine = setup_client(database_url, tmp_path)
    engine.update_execution_options(isolation_level=default_isolation)
    ready = Barrier(2)
    levels = []
    original = SqlProjectUnitOfWork.lock_owner

    def both_arrived(self, actor):
        levels.append(self.db.scalar(text("SHOW transaction_isolation")))
        ready.wait(timeout=10)
        return original(self, actor)

    monkeypatch.setattr(SqlProjectUnitOfWork, "lock_owner", both_arrived)
    try:
        with client:
            headers = [authorization(client), authorization(client)]
            seed_projects(engine, 99)
            with ThreadPoolExecutor(max_workers=2) as pool:
                responses = list(
                    pool.map(
                        lambda actor: client.post(PATH, headers=actor, json={"title": "Last slot"}),
                        headers,
                    )
                )
            assert levels == ["read committed", "read committed"]
            assert sorted(r.status_code for r in responses) == [201, 429]
            limited = next(r for r in responses if r.status_code == 429)
            assert limited.json()["error"]["code"] == "QUOTA_EXCEEDED"
            assert limited.headers["Retry-After"] == "86400"
            with engine.connect() as db:
                assert db.scalar(text("SELECT count(*) FROM projects")) == 100
    finally:
        engine.dispose()


def test_create_rolls_back_if_commit_fails(database_url, tmp_path, monkeypatch):
    from forma_backend.infrastructure.storage.maintenance import MaintenanceGuard
    from forma_backend.modules.project_files.storage import StorageUnavailable

    client, engine = setup_client(database_url, tmp_path)

    def failed(self):
        raise StorageUnavailable()

    try:
        with client:
            headers = authorization(client)
            monkeypatch.setattr(MaintenanceGuard, "commit", failed)
            response = client.post(PATH, headers=headers, json={"title": "Rollback"})
            assert (
                response.status_code == 503
                and response.json()["error"]["code"] == "STORAGE_UNAVAILABLE"
            )
            with engine.connect() as db:
                assert db.scalar(text("SELECT count(*) FROM projects")) == 0
    finally:
        engine.dispose()


@pytest.mark.parametrize("invalidate", ["password", "disabled", "expired"])
def test_invalidated_actor_cannot_create_after_wait(
    database_url, tmp_path, monkeypatch, invalidate
):
    from forma_backend.infrastructure.projects.persistence import SqlProjectUnitOfWork

    client, engine = setup_client(database_url, tmp_path)
    arrived, release = Event(), Event()
    original = SqlProjectUnitOfWork.lock_owner

    def delayed(self, actor):
        arrived.set()
        assert release.wait(10)
        return original(self, actor)

    try:
        with client:
            headers = authorization(client)
            monkeypatch.setattr(SqlProjectUnitOfWork, "lock_owner", delayed)
            with ThreadPoolExecutor(max_workers=1) as pool:
                creating = pool.submit(
                    client.post, PATH, headers=headers, json={"title": "Stale actor"}
                )
                try:
                    assert arrived.wait(10)
                    if invalidate == "password":
                        changed = client.post(
                            "/api/v1/users/me/change-password",
                            headers=headers,
                            json={
                                "current_password": "correct horse battery",
                                "new_password": "new strong account password",
                            },
                        )
                        assert changed.status_code == 204
                    else:
                        sql = (
                            "UPDATE users SET is_active=false"
                            if invalidate == "disabled"
                            else "UPDATE auth_sessions SET created_at=now()-interval '2 minutes',expires_at=now()-interval '1 minute'"
                        )
                        with engine.begin() as db:
                            db.execute(text(sql))
                finally:
                    release.set()
                assert creating.result(timeout=10).status_code == 401
            with engine.connect() as db:
                assert db.scalar(text("SELECT count(*) FROM projects")) == 0
    finally:
        release.set()
        engine.dispose()


def test_project_migration_preserves_seeded_identity_and_enforces_staged_constraints(
    database_url, monkeypatch
):
    from alembic import command
    from sqlalchemy import inspect
    from sqlalchemy.exc import IntegrityError
    from forma_backend.infrastructure.database.session import create_database_engine
    from test_migrations import config

    engine = create_database_engine(database_url)
    owner = uuid4()
    try:
        with engine.begin() as db:
            command.upgrade(config(db), "0002_sessions_limits")
            db.execute(
                text(
                    "INSERT INTO users(id,email,password_hash,display_name) VALUES (:id,'seed@example.org','untouched-hash','Seed')"
                ),
                {"id": owner},
            )
            command.upgrade(config(db), "head")
            command.upgrade(config(db), "head")
            assert (
                db.scalar(text("SELECT password_hash FROM users WHERE id=:id"), {"id": owner})
                == "untouched-hash"
            )
            assert {"projects", "project_members"} <= set(inspect(db).get_table_names())
            assert "project_nodes" not in inspect(db).get_table_names()
            command.check(config(db))
        for sql, params in [
            (
                "INSERT INTO projects(id,owner_id,title) VALUES (:id,:owner,' ')",
                {"id": uuid4(), "owner": owner},
            ),
            (
                "INSERT INTO projects(id,owner_id,title,main_file_id) VALUES (:id,:owner,'bad main',:main)",
                {"id": uuid4(), "owner": owner, "main": uuid4()},
            ),
            (
                "INSERT INTO projects(id,owner_id,title) VALUES (:id,:owner,'missing owner')",
                {"id": uuid4(), "owner": uuid4()},
            ),
            (
                "INSERT INTO projects(id,owner_id,title,status) VALUES (:id,:owner,'bad status','deleted')",
                {"id": uuid4(), "owner": owner},
            ),
            (
                "INSERT INTO projects(id,owner_id,title,engine) VALUES (:id,:owner,'bad engine','shell')",
                {"id": uuid4(), "owner": owner},
            ),
        ]:
            with pytest.raises(IntegrityError):
                with engine.begin() as db:
                    db.execute(text(sql), params)
        project_id = uuid4()
        with engine.begin() as db:
            db.execute(
                text("INSERT INTO projects(id,owner_id,title) VALUES (:id,:owner,'Valid seed')"),
                {"id": project_id, "owner": owner},
            )
        for member, role, inviter in [
            (owner, "owner", owner),
            (uuid4(), "viewer", owner),
            (owner, "editor", uuid4()),
        ]:
            with pytest.raises(IntegrityError):
                with engine.begin() as db:
                    db.execute(
                        text(
                            "INSERT INTO project_members(project_id,user_id,role,invited_by) VALUES (:project,:member,:role,:inviter)"
                        ),
                        {"project": project_id, "member": member, "role": role, "inviter": inviter},
                    )
        monkeypatch.setenv("FORMA_ALLOW_DESTRUCTIVE_DOWNGRADE", "1")
        with engine.begin() as db:
            command.downgrade(config(db), "0002_sessions_limits")
            assert db.scalar(text("SELECT password_hash FROM users")) == "untouched-hash"
            command.upgrade(config(db), "head")
            command.check(config(db))
    finally:
        engine.dispose()


def test_orm_commit_cannot_escape_outer_guarded_transaction(database_url, tmp_path):
    from forma_backend.infrastructure.projects.persistence import SqlProjectUnitOfWork
    from forma_backend.modules.identity.sessions import Principal

    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            authorization(client)
            with engine.connect() as db:
                user, session = db.execute(text("SELECT user_id,id FROM auth_sessions")).one()
            with SqlProjectUnitOfWork(engine) as work:
                assert work.lock_owner(Principal(user, session))
                work.add(uuid4(), user, "Outer transaction", "")
                work.db.commit()
                with engine.connect() as reader:
                    assert reader.scalar(text("SELECT count(*) FROM projects")) == 0
                work.commit()
            with engine.connect() as reader:
                assert reader.scalar(text("SELECT count(*) FROM projects")) == 1
    finally:
        engine.dispose()


def test_deferred_database_commit_error_is_atomic_and_guard_reusable(database_url, tmp_path):
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            headers = authorization(client)
            with engine.begin() as db:
                db.execute(text("CREATE TABLE test_commit_target (id uuid PRIMARY KEY)"))
                db.execute(
                    text(
                        "ALTER TABLE projects ADD CONSTRAINT test_late_failure FOREIGN KEY(owner_id) REFERENCES test_commit_target(id) DEFERRABLE INITIALLY DEFERRED"
                    )
                )
            response = client.post(PATH, headers=headers, json={"title": "Deferred failure"})
            assert response.status_code == 503
            with engine.begin() as db:
                assert db.scalar(text("SELECT count(*) FROM projects")) == 0
                db.execute(text("ALTER TABLE projects DROP CONSTRAINT test_late_failure"))
            assert (
                client.post(
                    PATH, headers=headers, json={"title": "Retry after known rollback"}
                ).status_code
                == 201
            )
    finally:
        engine.dispose()


def test_owner_quota_is_separate_from_other_users_and_cookies(database_url, tmp_path):
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            owner_header = authorization(client)
            assert (
                client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": "other@example.org",
                        "password": "correct horse battery",
                        "display_name": "Other",
                    },
                ).status_code
                == 201
            )
            other_token = login(client, "other@example.org")
            with engine.begin() as db:
                db.execute(
                    text(
                        "INSERT INTO projects(id,owner_id,title) SELECT gen_random_uuid(),u.id,'Other retained' FROM users u CROSS JOIN generate_series(1,100) n WHERE email='other@example.org'"
                    )
                )
            response = client.post(
                PATH,
                headers={
                    **owner_header,
                    "Cookie": "forma_refresh=" + client.cookies.get("forma_refresh"),
                },
                json={"title": "Owner despite other cookie"},
            )
            assert response.status_code == 201
            other_header = {"Authorization": "Bearer " + other_token["access_token"]}
            assert (
                client.post(PATH, headers=other_header, json={"title": "Other full"}).status_code
                == 429
            )
            with engine.connect() as db:
                assert (
                    str(db.scalar(text("SELECT id FROM users WHERE email='owner@example.org'")))
                    == response.json()["owner_id"]
                )
    finally:
        engine.dispose()


def test_contended_owner_lock_times_out_without_partial_project(database_url, tmp_path):
    client, engine = setup_client(database_url, tmp_path)
    try:
        with client:
            headers = authorization(client)
            with ThreadPoolExecutor(max_workers=1) as pool:
                with engine.begin() as blocker:
                    blocker.execute(text("SELECT id FROM users FOR UPDATE"))
                    pending = pool.submit(
                        client.post, PATH, headers=headers, json={"title": "Busy owner"}
                    )
                    response = pending.result(timeout=6)
                    assert response.status_code == 503
            with engine.connect() as db:
                assert db.scalar(text("SELECT count(*) FROM projects")) == 0
            assert (
                client.post(PATH, headers=headers, json={"title": "After release"}).status_code
                == 201
            )
    finally:
        engine.dispose()
