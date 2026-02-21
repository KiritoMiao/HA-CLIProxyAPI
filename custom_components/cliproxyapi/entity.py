"""Shared entity helpers for CLIProxyAPI integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_BASE_URL, DOMAIN
from .coordinator import CLIProxyAPIDataUpdateCoordinator


class CLIProxyAPIEntity(CoordinatorEntity[CLIProxyAPIDataUpdateCoordinator]):
    """Base class for all CLIProxyAPI entities.

    All entities created for one config entry share a single device identifier,
    so one CLIProxyAPI site appears as one device in Home Assistant.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: CLIProxyAPIDataUpdateCoordinator,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about this integration device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title or "CLIProxyAPI",
            manufacturer="Kirito",
            configuration_url=self._entry.data.get(CONF_BASE_URL),
        )
