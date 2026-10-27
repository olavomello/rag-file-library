"""Integration tests for local filesystem document storage."""

from __future__ import annotations

from pathlib import Path

import pytest

from private_rag.application.services.naming import (
    UnsafeStoredNameError,
    build_stored_name,
)
from private_rag.infrastructure.filesystem.file_storage import FileStorage


@pytest.fixture
def storage(tmp_path: Path) -> FileStorage:
    store = FileStorage(tmp_path / "uploads")
    store.ensure_ready()
    return store


def test_save_and_read_roundtrip(storage: FileStorage) -> None:
    payload = b"hello \xe2\x9c\x93 world"
    storage.save("doc-1.txt", payload)
    assert storage.exists("doc-1.txt")
    assert storage.read("doc-1.txt") == payload


def test_save_overwrites_atomically(storage: FileStorage) -> None:
    storage.save("doc-1.txt", b"v1")
    storage.save("doc-1.txt", b"v2")
    assert storage.read("doc-1.txt") == b"v2"


def test_delete_is_idempotent(storage: FileStorage) -> None:
    storage.save("doc-1.txt", b"data")
    storage.delete("doc-1.txt")
    assert not storage.exists("doc-1.txt")
    storage.delete("doc-1.txt")  # no error on missing


@pytest.mark.parametrize(
    "name",
    ["../escape.txt", "sub/dir.txt", "..", "", "a\\b.txt"],
)
def test_path_traversal_and_unsafe_names_rejected(storage: FileStorage, name: str) -> None:
    with pytest.raises(UnsafeStoredNameError):
        storage.save(name, b"x")


def test_build_stored_name_uses_id_not_client_name() -> None:
    assert build_stored_name("doc-1", ".PDF") == "doc-1.pdf"
    assert build_stored_name("doc-1", "txt") == "doc-1.txt"


def test_build_stored_name_rejects_unsafe_extension() -> None:
    with pytest.raises(UnsafeStoredNameError):
        build_stored_name("doc-1", ".tar.gz/../x")
