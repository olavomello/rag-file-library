"""Downloads (pulls) a model into a local Ollama instance, streaming progress."""

from __future__ import annotations

import json
from collections.abc import Iterator

import httpx

from private_rag.application.exceptions import ModelPullError


class OllamaModelPuller:
    """Streams ``/api/pull`` progress from Ollama while a model is downloaded.

    A pull can transfer gigabytes and take a long time, so no read timeout is
    applied (only a short connect timeout). An ``httpx.Client`` may be injected
    for testing. Failures surface as :class:`ModelPullError`.
    """

    def __init__(
        self,
        *,
        base_url: str,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client

    def stream_pull(self, model: str) -> Iterator[dict[str, object]]:
        url = f"{self._base_url}/api/pull"
        payload = {"model": model, "stream": True}
        client = self._client or httpx.Client(
            timeout=httpx.Timeout(10.0, read=None, write=None, pool=None)
        )
        owns_client = self._client is None
        try:
            with client.stream("POST", url, json=payload) as response:
                if response.status_code != httpx.codes.OK:
                    raise ModelPullError(f"Ollama returned HTTP {response.status_code}")
                for line in response.iter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    error = data.get("error")
                    if error:
                        raise ModelPullError(str(error))
                    yield {
                        "status": str(data.get("status", "")),
                        "completed": data.get("completed"),
                        "total": data.get("total"),
                    }
        except httpx.HTTPError as exc:
            raise ModelPullError(
                f"Ollama pull request failed: {exc.__class__.__name__}"
            ) from exc
        finally:
            if owns_client:
                client.close()
