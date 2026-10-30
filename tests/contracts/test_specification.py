"""Phase A specification tests, not implemented API tests."""

import json
import re
import subprocess
import sys
from pathlib import Path
import pytest
from openapi_spec_validator import validate
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from docs.contracts import models as m
from docs.contracts.registry import ROWS


def test_openapi_valid():
    validate(json.loads((ROOT / "docs/contracts/openapi.json").read_text()))


def test_generated_artifacts_fresh():
    paths = (
        list((ROOT / "docs/api").glob("*.md"))
        + list((ROOT / "docs/contracts").glob("*.json"))
        + [ROOT / "docs/09_API_ENDPOINT_CATALOG.md"]
        + list((ROOT / "docs/examples").glob("*.json"))
    )
    before = {p: p.read_bytes() for p in paths}
    subprocess.run([sys.executable, str(ROOT / "scripts/build_contracts.py")], check=True)
    assert all(p.read_bytes() == b for p, b in before.items())


def test_registry_and_dag_complete():
    es = json.loads((ROOT / "docs/contracts/endpoints.json").read_text())
    tasks = json.loads((ROOT / "docs/tasks/tasks.json").read_text())
    assert len(es) == 46 and len({(e["method"], e["path"]) for e in es}) == 46
    assert len(tasks) == 52 and {t["id"] for t in tasks} == {f"BE-{n:03}" for n in range(1, 53)}
    tables = set(json.loads((ROOT / "docs/database/tables.json").read_text()))
    pending = {t["id"]: set(t["depends_on"]) for t in tasks}
    done = set()
    while pending:
        ready = {k for k, v in pending.items() if v <= done}
        assert ready, "DAG cycle or missing dependency"
        done |= ready
        for k in ready:
            del pending[k]
    for e in es:
        assert e["task"] in done
        assert set(e["tables"]) <= tables
        assert len(e["tests"]) == 4
        assert (ROOT / f"docs/tasks/TASK-{e['task']}.md").is_file()


def test_examples_validate_against_dto():
    spec = json.loads((ROOT / "docs/contracts/openapi.json").read_text())
    for method, path, req, res, *_ in ROWS:
        op = spec["paths"][path][method.lower()]
        if req and req is not m.Upload:
            req.model_validate(op["requestBody"]["content"]["application/json"]["example"])
        if res and res is not m.Binary:
            for response in op["responses"].values():
                media = response.get("content", {}).get("application/json", {})
                if "example" in media:
                    res.model_validate(media["example"])


@pytest.mark.parametrize(
    "model,payload",
    [
        (m.SaveContent, {"content": "text", "expected_revision": 0}),
        (m.MemberPatch, {"role": "owner"}),
        (m.Register, {"email": "invalid", "password": "short", "display_name": "a"}),
        (m.SettingsPatch, {"main_file_id": None, "engine": "shell", "expected_revision": 1}),
        (m.SaveContent, {"content": "text", "expected_revision": 1, "overwrite": True}),
    ],
)
def test_invalid_wire_inputs(model, payload):
    with pytest.raises(ValidationError):
        model.model_validate(payload)


def test_local_markdown_links():
    missing = []
    for p in [*ROOT.glob("*.md"), *ROOT.joinpath("docs").rglob("*.md")]:
        for link in re.findall(r"\]\(([^)]+)\)", p.read_text()):
            link = link.split("#")[0]
            if not link or "://" in link or link.startswith("mailto:"):
                continue
            if not (p.parent / link).exists():
                missing.append(f"{p.relative_to(ROOT)} -> {link}")
    assert not missing, "\n".join(missing)


def test_dictionary_covers_sql_columns():
    sql = (ROOT / "docs/database/schema.sql").read_text()
    dictionary = (ROOT / "docs/06_DATABASE_DICTIONARY.md").read_text()
    for table, body in re.findall(r"CREATE TABLE (\w+) \(\n(.*?)\n\);", sql, re.S):
        section = dictionary.split("## " + table + "\n")[1].split("\n## ")[0]
        for line in body.splitlines():
            key = line.strip().split()[0]
            if key not in ["CHECK", "UNIQUE", "PRIMARY", "FOREIGN"]:
                assert f"`{key}`" in section
