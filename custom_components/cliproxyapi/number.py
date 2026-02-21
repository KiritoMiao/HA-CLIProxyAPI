"""Number entities for CLIProxyAPI numeric controls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import CLIProxyAPIClient
from .const import DATA_API_CLIENT, DATA_COORDINATOR, DOMAIN
from .coordinator import CLIProxyAPIDataUpdateCoordinator
from .entity import CLIProxyAPIEntity


@dataclass(frozen=True, kw_only=True)
class CLIProxyAPINumberDescription(NumberEntityDescription):
    """Describes a CLIProxyAPI number entity."""

    value_fn: Callable[[dict[str, Any]], float]
    setter_name: str


NUMBER_DESCRIPTIONS: tuple[CLIProxyAPINumberDescription, ...] = (
    CLIProxyAPINumberDescription(
        key="request_retry",
        translation_key="request_retry",
        icon="mdi:restore-alert",
        native_min_value=0,
        native_max_value=10,
        native_step=1,
        native_unit_of_measurement="attempts",
        value_fn=lambda data: float(data.get("settings", {}).get("request_retry", 0)),
        setter_name="set_request_retry",
    ),
    CLIProxyAPINumberDescription(
        key="max_retry_interval",
        translation_key="max_retry_interval",
        icon="mdi:timer-cog-outline",
        native_min_value=1,
        native_max_value=600,
        native_step=1,
        native_unit_of_measurement="s",
        value_fn=lambda data: float(
            data.get("settings", {}).get("max_retry_interval", 0)
        ),
        setter_name="set_max_retry_interval",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities."""
    runtime = hass.data[DOMAIN][entry.entry_id]
    coordinator: CLIProxyAPIDataUpdateCoordinator = runtime[DATA_COORDINATOR]
    api: CLIProxyAPIClient = runtime[DATA_API_CLIENT]

    async_add_entities(
        CLIProxyAPINumber(entry, coordinator, api, description)
        for description in NUMBER_DESCRIPTIONS
    )


class CLIProxyAPINumber(CLIProxyAPIEntity, NumberEntity):
    """Representation of CLIProxyAPI number controls."""

    entity_description: CLIProxyAPINumberDescription
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: CLIProxyAPIDataUpdateCoordinator,
        api: CLIProxyAPIClient,
        description: CLIProxyAPINumberDescription,
    ) -> None:
        """Initialize number entity."""
        super().__init__(entry, coordinator, description.key)
        self._api = api
        self.entity_description = description

    @property
    def native_value(self) -> float:
        """Return number state value."""
        data = self.coordinator.data or {}
        return self.entity_description.value_fn(data)

    async def async_set_native_value(self, value: float) -> None:
        """Set number value."""
        await getattr(self._api, self.entity_description.setter_name)(int(value))
        await self.coordinator.async_request_refresh()
