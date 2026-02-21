"""Binary sensor entities for CLIProxyAPI."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import CLIProxyAPIDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities from config entry."""
    coordinator: CLIProxyAPIDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities([CLIProxyAPIReachableBinarySensor(coordinator, entry.entry_id)])


class CLIProxyAPIReachableBinarySensor(
    CoordinatorEntity[CLIProxyAPIDataUpdateCoordinator], BinarySensorEntity
):
    """Indicates if Home Assistant can currently reach CLIProxyAPI."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_translation_key = "reachable"
    _attr_icon = "mdi:lan-connect"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: CLIProxyAPIDataUpdateCoordinator, entry_id: str
    ) -> None:
        """Initialize reachability entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_reachable"

    @property
    def is_on(self) -> bool:
        """Return True when coordinator updates are successful."""
        return self.coordinator.last_update_success
