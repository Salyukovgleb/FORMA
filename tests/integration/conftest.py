"""Real PostgreSQL only; every test owns a new UUID-named disposable database."""

import os
import secrets
import subprocess
import time
from uuid import uuid4

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from sqlalchemy import URL


@pytest.fixture(scope="session")
def postgres_admin():
    supplied = os.environ.get("FORMA_TEST_DATABASE_URL")
    if supplied:
        params = conninfo_to_dict(supplied)
        if params.get("dbname") != "forma_contract_test":
            raise RuntimeError("Only dedicated forma_contract_test may supply the test server")
        yield make_conninfo(**{**params, "dbname": "postgres"})
        return
    name = "forma-migrations-" + uuid4().hex[:12]
    password = secrets.token_hex(24)
    image = "postgres:16.6@sha256:557fea37a744d5f4c8faab304b0a90858b53ab119735a88c131fd19dab802f36"
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-d",
            "--name",
            name,
            "-e",
            "POSTGRES_PASSWORD",
            "-p",
            "127.0.0.1::5432",
            image,
        ],
        env={**os.environ, "POSTGRES_PASSWORD": password},
        check=True,
        capture_output=True,
    )
    try:
        port = (
            subprocess.check_output(["docker", "port", name, "5432/tcp"], text=True)
            .strip()
            .split(":")[-1]
        )
        info = make_conninfo(
            host="127.0.0.1", port=port, user="postgres", password=password, dbname="postgres"
        )
        deadline = time.monotonic() + 90
        while True:
            try:
                with psycopg.connect(info):
                    pass
                break
            except psycopg.OperationalError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.25)
        yield info
    finally:
        subprocess.run(["docker", "rm", "-f", "-v", name], check=True, capture_output=True)


@pytest.fixture
def database_url(postgres_admin):
    name = "forma_migration_test_" + uuid4().hex
    params = conninfo_to_dict(postgres_admin)
    with psycopg.connect(postgres_admin, autocommit=True) as conn:
        conn.execute(psycopg.sql.SQL("CREATE DATABASE {}").format(psycopg.sql.Identifier(name)))
    try:
        yield URL.create(
            "postgresql+psycopg",
            username=params.get("user"),
            password=params.get("password"),
            host=params.get("host"),
            port=int(params["port"]),
            database=name,
        )
    finally:
        with psycopg.connect(postgres_admin, autocommit=True) as conn:
            conn.execute(
                psycopg.sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                    psycopg.sql.Identifier(name)
                )
            )
