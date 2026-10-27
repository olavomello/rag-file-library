"""Export the FastAPI OpenAPI schema to ``backend/openapi.json``.

The committed spec is importable into Insomnia, Postman, and other OpenAPI
readers. Regenerate it whenever an endpoint is added, changed, or removed:

    uv run python scripts/export_openapi.py

A contract test (tests/contract/test_openapi_current.py) fails if the committed
file is out of date, so CI enforces that it stays current.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from private_rag.main import create_app
from private_rag.settings import Settings

OUTPUT = Path(__file__).resolve().parents[1] / "openapi.json"


def build_openapi() -> dict[str, Any]:
    """Build the OpenAPI schema deterministically (settings-independent)."""
    app = create_app(settings=Settings(_env_file=None))
    schema: dict[str, Any] = app.openapi()
    return schema


def serialize(schema: dict[str, Any]) -> str:
    return json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> None:
    OUTPUT.write_text(serialize(build_openapi()), encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
