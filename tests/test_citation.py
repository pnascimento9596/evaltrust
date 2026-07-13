import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_citation_version_matches_pyproject():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    expected = pyproject["project"]["version"]
    # Regex not YAML parse — avoids a PyYAML dep; CFF `version` is
    # always a top-level flat scalar, so it can't misfire. Upgrade to a real
    # YAML parse only if the field ever becomes nested/multi-line.
    cff = (ROOT / "CITATION.cff").read_text()
    match = re.search(r"^version:\s*(.+)$", cff, re.MULTILINE)
    assert match, "no version: line in CITATION.cff"
    actual = match.group(1).strip().strip('"')
    assert actual == expected, (
        f"CITATION.cff version ({actual}) != pyproject.toml version ({expected}); "
        f"bump CITATION.cff to {expected}"
    )
