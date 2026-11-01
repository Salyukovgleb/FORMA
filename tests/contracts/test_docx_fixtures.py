"""Corpus integrity only; conversion fidelity is a future isolated exporter gate."""

import json
import re
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "tests/fixtures/docx"


def test_docx_matrix_has_complete_source_cases():
    manifest = json.loads((CORPUS / "manifest.json").read_text())
    assert manifest["version"] == 1
    cases = manifest["cases"]
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)) == 18
    matrix = (ROOT / "docs/13_DOCX_EXPORT.md").read_text()
    documented = re.findall(r"`(DX-\d+)`", matrix)
    assert set(documented) == set(ids)
    for case in cases:
        assert case["support"] in {"supported", "partial", "unsupported"}
        assert case["assertions"]
        source = (CORPUS / case["source"]).read_text(encoding="utf-8")
        assert r"\begin{document}" in source and r"\end{document}" in source
        for asset in re.findall(r"\\includegraphics\{([^}]+)\}", source):
            assert asset in case["assets"]
        for needle in case["source_markers"]:
            assert needle in source
        for relative in [case["source"], *case["assets"]]:
            path = PurePosixPath(relative)
            assert not path.is_absolute() and ".." not in path.parts
            target = CORPUS / path
            assert target.is_file() and not target.is_symlink()
            assert CORPUS.resolve() in target.resolve().parents
            assert target.stat().st_size > 0
        if case["support"] != "supported":
            assert case["warnings"]
        for warning in case["warnings"]:
            assert warning["code"].startswith("DOCX_")
            assert warning["file"] == case["source"]
            assert 1 <= warning["line"] <= len(source.splitlines())
            assert warning["marker"] in source.splitlines()[warning["line"] - 1]


def test_custom_macro_has_located_warning_and_visible_placeholder():
    cases = json.loads((CORPUS / "manifest.json").read_text())["cases"]
    custom = next(c for c in cases if c["id"] == "DX-017")
    assert custom["support"] == "unsupported"
    assert custom["warnings"][0]["code"] == "DOCX_UNSUPPORTED_CONSTRUCT"
    assert custom["warnings"][0]["marker"] == r"\customforma"
    assert "visible placeholder with warning; no silent loss" in custom["assertions"]
