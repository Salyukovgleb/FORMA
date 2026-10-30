"""Reject installed dependency versions that differ from the committed lock."""

import re
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def check(path: Path) -> list[str]:
    errors = []
    pins = re.findall(r"^([\w.-]+)==([^\s\\]+)", path.read_text(), re.MULTILINE)
    if not pins:
        return ["Lock contains no pinned dependencies"]
    for name, expected in pins:
        try:
            actual = version(name)
        except PackageNotFoundError:
            actual = "missing"
        if actual != expected:
            errors.append(f"{name}: expected {expected}, installed {actual}")
    return errors


if __name__ == "__main__":
    path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).resolve().parents[1] / "requirements-dev.lock"
    )
    errors = check(path)
    for error in errors:
        print(error, file=sys.stderr)
    print("Dependency lock: " + ("FAIL" if errors else "PASS"))
    raise SystemExit(bool(errors))
