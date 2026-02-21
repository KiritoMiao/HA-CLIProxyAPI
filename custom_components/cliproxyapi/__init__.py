"""Home Assistant integration setup for CLIProxyAPI."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CLIProxyAPIClient
from .const import (
    CONF_BASE_URL,
    CONF_ENABLE_LOG_DIAGNOSTICS,
    CONF_ENABLE_REQUEST_ERROR_LOGS,
    CONF_MANAGEMENT_KEY,
    CONF_POLL_INTERVAL_SECONDS,
    DEFAULT_ENABLE_LOG_DIAGNOSTICS,
    DEFAULT_ENABLE_REQUEST_ERROR_LOGS,
    DATA_API_CLIENT,
    DATA_COORDINATOR,
    DOMAIN,
    PLATFORMS,
    UPDATE_INTERVAL_SECONDS,
)
from .coordinator import CLIProxyAPIDataUpdateCoordinator


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up integration from YAML (not used)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up CLIProxyAPI from a config entry."""
    session = async_get_clientsession(hass)
    api = CLIProxyAPIClient(
        session=session,
        base_url=entry.data[CONF_BASE_URL],
        management_key=entry.data[CONF_MANAGEMENT_KEY],
    )
    coordinator = CLIProxyAPIDataUpdateCoordinator(
        hass,
        api,
        poll_interval_seconds=int(
            entry.options.get(CONF_POLL_INTERVAL_SECONDS, UPDATE_INTERVAL_SECONDS)
        ),
        enable_log_diagnostics=bool(
            entry.options.get(
                CONF_ENABLE_LOG_DIAGNOSTICS,
                DEFAULT_ENABLE_LOG_DIAGNOSTICS,
            )
        ),
        enable_request_error_logs=bool(
            entry.options.get(
                CONF_ENABLE_REQUEST_ERROR_LOGS,
                DEFAULT_ENABLE_REQUEST_ERROR_LOGS,
            )
        ),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_API_CLIENT: api,
        DATA_COORDINATOR: coordinator,
    }
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
