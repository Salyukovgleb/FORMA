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
    env.update(
        {
            "DATABASE_URL": f"postgresql+psycopg://forma:{env['POSTGRES_PASSWORD']}@postgres:5432/forma",
            "JWT_SECRET": secrets.token_hex(32),
            "APP_ENV": "test",
            "JWT_KEY_ID": "v1",
            "JWT_PREVIOUS_KEY_ID": "",
            "JWT_PREVIOUS_SECRET": "",
            "ALLOWED_ORIGINS": "https://forma.example.org",
            "COOKIE_SECURE": "true",
        }
    )
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
                + (result.stdout + result.stderr)[-18000:].replace(
                    env["POSTGRES_PASSWORD"], "[redacted]"
                )
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
        heads = run(
            "run",
            "--rm",
            "--no-deps",
            "backend",
            "python",
            "-m",
            "alembic",
            "-c",
            "/opt/forma/alembic.ini",
            "heads",
        )
        assert "0002_sessions_limits (head)" in heads
        run("up", "-d", "--wait", "--wait-timeout", "90", "api")
        run(
            "exec",
            "-T",
            "api",
            "python",
            "-c",
            "import json,urllib.request; "
            "assert json.load(urllib.request.urlopen('http://127.0.0.1:8000/health/live')) == {'status':'ok'}; "
            "assert json.load(urllib.request.urlopen('http://127.0.0.1:8000/health/ready')) == {'status':'ok'}",
        )
        run(
            "run",
            "--rm",
            "--no-deps",
            "backend",
            "python",
            "-c",
            "from forma_backend.infrastructure.identity.passwords import ScryptPasswordHasher; "
            "h=ScryptPasswordHasher(); assert h.verify('runtime-password',h.hash('runtime-password'))",
        )
        run(
            "run",
            "--rm",
            "--no-deps",
            "-e",
            "DATABASE_URL",
            "backend",
            "python",
            "-m",
            "alembic",
            "-c",
            "/opt/forma/alembic.ini",
            "upgrade",
            "head",
        )
        run(
            "exec",
            "-T",
            "api",
            "python",
            "-c",
            "import json,urllib.request; from http.cookies import SimpleCookie; "
            "url='http://127.0.0.1:8000'; headers={'Content-Type':'application/json','Origin':'https://forma.example.org'}; "
            "register={'email':'smoke@example.org','password':'correct horse battery','display_name':'Smoke'}; "
            "r=urllib.request.urlopen(urllib.request.Request(url+'/api/v1/auth/register',data=json.dumps(register).encode(),headers=headers)); assert r.status==201; "
            "r=urllib.request.urlopen(urllib.request.Request(url+'/api/v1/auth/login',data=json.dumps({k:v for k,v in register.items() if k!='display_name'}).encode(),headers=headers)); "
            "token=json.load(r); cookie=SimpleCookie(r.headers['Set-Cookie']); assert cookie['forma_refresh']['httponly'] and cookie['forma_refresh']['secure']; "
            "r=urllib.request.urlopen(urllib.request.Request(url+'/api/v1/auth/refresh',method='POST',headers={**headers,'X-CSRF-Token':token['csrf_token'],'Cookie':'forma_refresh='+cookie['forma_refresh'].value})); fresh=json.load(r); "
            "r=urllib.request.urlopen(urllib.request.Request(url+'/api/v1/auth/sessions',headers={'Authorization':'Bearer '+fresh['access_token']})); "
            "assert json.load(r)['items'][0]['is_current']; "
            "bearer={**headers,'Authorization':'Bearer '+fresh['access_token']}; "
            "r=urllib.request.urlopen(urllib.request.Request(url+'/api/v1/users/me',headers=bearer)); assert json.load(r)['email']=='smoke@example.org'; "
            "r=urllib.request.urlopen(urllib.request.Request(url+'/api/v1/users/me',method='PATCH',data=json.dumps({'display_name':'Updated'}).encode(),headers=bearer)); assert json.load(r)['display_name']=='Updated'; "
            "r=urllib.request.urlopen(urllib.request.Request(url+'/api/v1/users/me/change-password',data=json.dumps({'current_password':register['password'],'new_password':'another strong smoke password'}).encode(),headers=bearer)); assert r.status==204",
        )
        cleaned = run(
            "exec",
            "-T",
            "api",
            "python",
            "-m",
            "forma_backend.infrastructure.identity.cleanup_limits",
            "--max-rows",
            "10",
        )
        assert cleaned.strip() == "removed=0"
        print(
            "PASS: non-root package image, PostgreSQL health, DB/files persistence across recreation, missing-secret rejection, live API health/ready"
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
