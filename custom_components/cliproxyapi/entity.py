"""Shared entity helpers for CLIProxyAPI integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CLIProxyAPIDataUpdateCoordinator


class CLIProxyAPIEntity(CoordinatorEntity[CLIProxyAPIDataUpdateCoordinator]):
    """Base class for all CLIProxyAPI entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CLIProxyAPIDataUpdateCoordinator,
        entry_id: str,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about this integration device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="CLIProxyAPI",
            manufacturer="Kirito",
        )
