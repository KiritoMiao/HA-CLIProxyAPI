"""Binary sensor entities for CLIProxyAPI."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import CLIProxyAPIDataUpdateCoordinator
from .entity import CLIProxyAPIEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities from config entry."""
    coordinator: CLIProxyAPIDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities([CLIProxyAPIReachableBinarySensor(entry, coordinator)])


class CLIProxyAPIReachableBinarySensor(CLIProxyAPIEntity, BinarySensorEntity):
    """Indicates if Home Assistant can currently reach CLIProxyAPI."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_translation_key = "reachable"
    _attr_icon = "mdi:lan-connect"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, entry: ConfigEntry, coordinator: CLIProxyAPIDataUpdateCoordinator
    ) -> None:
        """Initialize reachability entity."""
        super().__init__(entry, coordinator, "reachable")

    @property
    def is_on(self) -> bool:
        """Return True when coordinator updates are successful."""
        return self.coordinator.last_update_success
