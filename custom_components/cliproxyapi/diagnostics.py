"""Diagnostics support for CLIProxyAPI integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_MANAGEMENT_KEY, DATA_COORDINATOR, DOMAIN

TO_REDACT = {
    CONF_MANAGEMENT_KEY,
    "Authorization",
    "X-Management-Key",
    "api-key",
    "cookie",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    payload = {
        "entry": dict(entry.data),
        "coordinator_data": coordinator.data,
    }
    return async_redact_data(payload, TO_REDACT)
