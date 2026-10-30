"""Installed package contract: import must work outside the checkout."""

import subprocess
import sys
from pathlib import Path


def test_installed_package_is_typed(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "from importlib.metadata import version; "
            "from importlib.resources import files; "
            "import forma_backend; "
            'assert version("forma-backend") == forma_backend.__version__; '
            'assert files("forma_backend").joinpath("py.typed").is_file()',
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_lock_rejects_wrong_installed_version(tmp_path: Path) -> None:
    lock = tmp_path / "wrong.lock"
    lock.write_text("pydantic==0.0.0\n")
    checker = Path(__file__).resolve().parents[2] / "scripts/check_lock.py"
    result = subprocess.run(
        [sys.executable, str(checker), str(lock)], capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "pydantic: expected 0.0.0" in result.stderr
