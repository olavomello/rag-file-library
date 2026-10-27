"""Contract test: the committed openapi.json must match the live API schema.

If this fails, an endpoint changed without regenerating the spec. Run:

    uv run python scripts/export_openapi.py
"""

from __future__ import annotations

import json
from pathlib import Path

from private_rag.main import create_app
from private_rag.settings import Settings

OPENAPI_FILE = Path(__file__).resolve().parents[2] / "openapi.json"


def test_committed_openapi_matches_app() -> None:
    assert OPENAPI_FILE.is_file(), "openapi.json is missing; run scripts/export_openapi.py"

    committed = json.loads(OPENAPI_FILE.read_text(encoding="utf-8"))
    current = create_app(settings=Settings(_env_file=None)).openapi()

    assert committed == current, (
        "openapi.json is out of date. Regenerate it with: "
        "uv run python scripts/export_openapi.py"
    )
