"""Real persistence smoke in an isolated, disposable Compose project."""

import os
import secrets
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    project = "forma-smoke-" + uuid4().hex[:12]
    env = {
        **os.environ,
        "POSTGRES_PASSWORD": secrets.token_hex(24),
        "FORMA_IMAGE": project + ":test",
    }
    base = [
        "docker",
        "compose",
        "--env-file",
        os.devnull,
        "-p",
        project,
        "-f",
        str(ROOT / "infra/compose.yaml"),
    ]

    def run(*args: str) -> str:
        result = subprocess.run(
            [*base, *args], env=env, cwd=ROOT, capture_output=True, text=True, timeout=300
        )
        if result.returncode:
            raise RuntimeError(
                "Compose failed: "
                + " ".join(args[:2])
                + "\n"
                + result.stderr.replace(env["POSTGRES_PASSWORD"], "[redacted]")
            )
        return result.stdout.strip()

    def sql(query: str) -> str:
        return run("exec", "-T", "postgres", "psql", "-U", "forma", "-d", "forma", "-Atc", query)

    run("config", "--quiet")
    try:
        bad = subprocess.run(
            [*base, "config", "--quiet"],
            env={**env, "POSTGRES_PASSWORD": ""},
            capture_output=True,
            timeout=30,
        )
        assert bad.returncode != 0, "Missing database password was accepted"
        run("build", "backend")
        run("up", "-d", "--wait", "--wait-timeout", "90", "postgres")
        old_id = run("ps", "-q", "postgres")
        sql(
            "CREATE TABLE persistence_probe (value text NOT NULL); INSERT INTO persistence_probe VALUES ('retained')"
        )
        run(
            "run",
            "--rm",
            "--no-deps",
            "backend",
            "python",
            "-c",
            "import os; from pathlib import Path; import forma_backend; assert os.getuid()==10001; Path('/var/lib/forma/probe').write_text('retained')",
        )
        run("up", "-d", "--force-recreate", "--wait", "--wait-timeout", "90", "postgres")
        assert run("ps", "-q", "postgres") != old_id, "PostgreSQL was not recreated"
        assert sql("SELECT value FROM persistence_probe") == "retained"
        run(
            "run",
            "--rm",
            "--no-deps",
            "backend",
            "python",
            "-c",
            "from pathlib import Path; assert Path('/var/lib/forma/probe').read_text()=='retained'",
        )
        print(
            "PASS: non-root package image, PostgreSQL health, DB/files persistence across recreation, missing-secret rejection"
        )
    finally:
        # Never use down -v. Remove only this invocation's labelled disposable volumes.
        subprocess.run(
            [*base, "down", "--remove-orphans"],
            env=env,
            capture_output=True,
            timeout=60,
            check=True,
        )
        volumes = subprocess.run(
            [
                "docker",
                "volume",
                "ls",
                "-q",
                "--filter",
                f"label=com.docker.compose.project={project}",
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        for volume in volumes:
            subprocess.run(["docker", "volume", "rm", volume], capture_output=True, check=True)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
