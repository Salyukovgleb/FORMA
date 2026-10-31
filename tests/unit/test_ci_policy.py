"""Guard the mandatory quality gates and token permissions against accidental removal."""

from pathlib import Path

import yaml
import re

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = {
    "lint",
    "types",
    "unit-tests",
    "integration-tests",
    "migration-check",
    "security-tests",
    "docker-build",
    "docs-contract",
}


def test_ci_quality_gates_are_unconditional_and_least_privilege():
    workflow = yaml.load((ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)
    assert REQUIRED <= set(workflow["jobs"])
    assert workflow["permissions"] == {"contents": "read"}
    assert "pull_request" in workflow["on"] and "push" in workflow["on"]
    assert "pull_request_target" not in workflow["on"]
    assert "main" in workflow["on"]["push"]["branches"]
    assert workflow["concurrency"]["cancel-in-progress"] == "true"
    for job in workflow["jobs"].values():
        assert "if" not in job and "continue-on-error" not in job
        assert 1 <= int(job["timeout-minutes"]) <= 15
        commands = [step["run"] for step in job["steps"] if "run" in step]
        assert any(
            "pytest" in c or c.startswith("make ") or "scripts/check_compose.py" in c
            for c in commands
        )
        for step in job["steps"]:
            assert "continue-on-error" not in step
            if "run" in step:
                assert "|| true" not in step["run"]
            if "uses" in step and not step["uses"].startswith("./"):
                assert re.fullmatch(r"[0-9a-f]{40}", step["uses"].split("@")[-1])
    assert "secrets." not in (ROOT / ".github/workflows/ci.yml").read_text()
