"""Architecture-boundary tests enforcing Clean Architecture dependency rules.

The domain layer must not import frameworks, I/O libraries, or outer layers; the
application layer must not import infrastructure/presentation or vendor clients.
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "private_rag"


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module)
    return modules


def _violations(layer: str, forbidden_prefixes: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for path in (SRC / layer).rglob("*.py"):
        for module in _imported_modules(path):
            if any(module == p or module.startswith(f"{p}.") for p in forbidden_prefixes):
                found.append(f"{path.relative_to(SRC)} imports {module}")
    return found


def test_domain_has_no_framework_io_or_outer_layer_imports() -> None:
    forbidden = (
        "fastapi",
        "chromadb",
        "pymupdf",
        "docx",
        "ollama",
        "httpx",
        "pydantic",
        "private_rag.application",
        "private_rag.infrastructure",
        "private_rag.presentation",
        "private_rag.container",
        "private_rag.settings",
    )
    assert _violations("domain", forbidden) == []


def test_application_does_not_import_infrastructure_or_presentation() -> None:
    forbidden = (
        "fastapi",
        "chromadb",
        "pymupdf",
        "docx",
        "ollama",
        "httpx",
        "private_rag.infrastructure",
        "private_rag.presentation",
        "private_rag.container",
    )
    assert _violations("application", forbidden) == []
