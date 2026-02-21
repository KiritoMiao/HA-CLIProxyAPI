"""Tests for config flow helpers."""

from __future__ import annotations

import pytest

pytest.importorskip("homeassistant")

from custom_components.cliproxyapi.config_flow import _normalize_base_url


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("127.0.0.1:8317", "http://127.0.0.1:8317"),
        ("http://127.0.0.1:8317/", "http://127.0.0.1:8317"),
        ("https://example.com/path", "https://example.com"),
    ],
)
def test_normalize_base_url(raw: str, expected: str) -> None:
    """Normalize base URLs into canonical host:port form."""
    assert _normalize_base_url(raw) == expected


def test_normalize_base_url_rejects_invalid() -> None:
    """Reject unsupported/invalid URLs."""
    with pytest.raises(ValueError):
        _normalize_base_url("ftp://example.com")

    with pytest.raises(ValueError):
        _normalize_base_url("http://")
