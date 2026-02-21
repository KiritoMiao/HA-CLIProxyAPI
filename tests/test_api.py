"""Tests for CLIProxyAPI API client."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import pytest

pytest.importorskip("homeassistant")

from custom_components.cliproxyapi.api import (
    CLIProxyAPIAuthenticationError,
    CLIProxyAPIClient,
)


class FakeResponse:
    """Simple aiohttp-like response object."""

    def __init__(
        self, status: int, payload: dict[str, Any] | None = None, text: str = ""
    ) -> None:
        self.status = status
        self._payload = payload
        self._text = text

    async def __aenter__(self) -> "FakeResponse":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def json(self, content_type: str | None = None) -> Any:
        if self._payload is None:
            raise ValueError("not json")
        return self._payload

    async def text(self) -> str:
        return self._text


class FakeSession:
    """Simple request dispatcher for tests."""

    def __init__(self) -> None:
        self.responses: dict[tuple[str, str], list[FakeResponse]] = defaultdict(list)
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def add(self, method: str, url: str, response: FakeResponse) -> None:
        self.responses[(method, url)].append(response)

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append((method, url, kwargs))
        queue = self.responses[(method, url)]
        if not queue:
            raise AssertionError(f"No fake response for {method} {url}")
        return queue.pop(0)


@pytest.mark.asyncio
async def test_get_and_set_debug() -> None:
    """Client can fetch and patch the debug toggle."""
    base = "http://127.0.0.1:8317"
    debug_url = f"{base}/v0/management/debug"

    session = FakeSession()
    session.add("GET", debug_url, FakeResponse(200, {"debug": True}))
    session.add("PATCH", debug_url, FakeResponse(200, {"status": "ok"}))

    client = CLIProxyAPIClient(session=session, base_url=base, management_key="secret")

    assert await client.get_debug() is True
    await client.set_debug(False)

    assert session.calls[1][0] == "PATCH"
    assert session.calls[1][2]["json"] == {"value": False}


@pytest.mark.asyncio
async def test_auth_failure_raises() -> None:
    """401/403 responses raise auth-specific exception."""
    base = "http://127.0.0.1:8317"
    debug_url = f"{base}/v0/management/debug"

    session = FakeSession()
    session.add(
        "GET", debug_url, FakeResponse(401, {"error": "invalid management key"})
    )

    client = CLIProxyAPIClient(session=session, base_url=base, management_key="bad")

    with pytest.raises(CLIProxyAPIAuthenticationError):
        await client.get_debug()


def test_forbidden_methods_not_exposed() -> None:
    """Client intentionally excludes constrained management operations."""
    session = FakeSession()
    client = CLIProxyAPIClient(
        session=session, base_url="http://127.0.0.1:8317", management_key="x"
    )

    assert not hasattr(client, "set_management_key")
    assert not hasattr(client, "set_port")
    assert not hasattr(client, "upload_auth_file")
    assert not hasattr(client, "start_oauth_login")
