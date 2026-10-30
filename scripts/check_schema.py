"""Validate design DDL in a fresh disposable PostgreSQL database; never use user DBs."""

import os
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path
import psycopg

ROOT = Path(__file__).resolve().parents[1]


def check(url: str) -> None:
    with psycopg.connect(url, autocommit=True) as conn:
        assert conn.execute("SELECT current_database()").fetchone()[0] == "forma_contract_test"
        assert (
            conn.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"
            ).fetchone()[0]
            == 0
        ), "Test DB must be empty"
        conn.execute((ROOT / "docs/database/schema.sql").read_text())
        conn.execute((ROOT / "docs/database/examples.sql").read_text())
        assert (
            conn.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"
            ).fetchone()[0]
            == 14
        )
        invalid = [
            "UPDATE users SET email='OWNER@example.org' WHERE email='owner@example.org'",
            "UPDATE project_members SET role='owner'",
            "UPDATE document_jobs SET state='running'",
            "UPDATE project_nodes SET logical_path='wrong.tex'",
            "UPDATE project_nodes SET node_type='folder', media_type=NULL",
            "DELETE FROM file_revisions",
            "UPDATE projects SET status='deleted'",
            "UPDATE file_revisions SET size_bytes=-1",
            "UPDATE project_nodes SET parent_id=id",
        ]
        for sql in invalid:
            try:
                with conn.transaction():
                    conn.execute(sql)
                    conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
            except psycopg.IntegrityError:
                pass
            else:
                raise AssertionError(f"Constraint accepted invalid data: {sql}")
        # A valid node from another project must not be assignable as main.
        with conn.transaction():
            conn.execute(
                "INSERT INTO projects(id,owner_id,title) VALUES('00000000-0000-4000-8000-000000000020','00000000-0000-4000-8000-000000000001','Other')"
            )
        try:
            with conn.transaction():
                conn.execute(
                    "UPDATE projects SET main_file_id='00000000-0000-4000-8000-000000000005' WHERE id='00000000-0000-4000-8000-000000000020'"
                )
                conn.execute("SET CONSTRAINTS ALL IMMEDIATE")
        except psycopg.IntegrityError:
            pass
        else:
            raise AssertionError("Cross-project main accepted")
        print(
            "PASS: DDL, 14 table fixtures, 10 negative integrity scenarios; PostgreSQL "
            + str(conn.info.server_version)
        )


def main() -> None:
    url = os.environ.get("FORMA_TEST_DATABASE_URL")
    if url:
        check(url)
        return
    for binary in ["initdb", "pg_ctl", "createdb"]:
        if not shutil.which(binary):
            raise SystemExit(
                f"Missing {binary}; use dedicated empty forma_contract_test via FORMA_TEST_DATABASE_URL"
            )
    with tempfile.TemporaryDirectory(prefix="forma-schema-") as tmp:
        data = Path(tmp) / "pg"
        sock = Path(tmp) / "socket"
        sock.mkdir()
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        subprocess.run(
            ["initdb", "-D", str(data), "-A", "trust", "--no-locale", "-E", "UTF8"],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        subprocess.run(
            [
                "pg_ctl",
                "-D",
                str(data),
                "-l",
                str(Path(tmp) / "postgres.log"),
                "-o",
                f"-k {sock} -p {port} -h 127.0.0.1",
                "-w",
                "start",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        try:
            subprocess.run(
                ["createdb", "-h", str(sock), "-p", str(port), "forma_contract_test"], check=True
            )
            check(f"host={sock} port={port} dbname=forma_contract_test")
        finally:
            subprocess.run(
                ["pg_ctl", "-D", str(data), "-m", "fast", "-w", "stop"],
                check=True,
                stdout=subprocess.DEVNULL,
            )


if __name__ == "__main__":
    main()
