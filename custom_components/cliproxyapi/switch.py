"""Switch entities for CLIProxyAPI configurable toggles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import CLIProxyAPIClient
from .const import DATA_API_CLIENT, DATA_COORDINATOR, DOMAIN
from .coordinator import CLIProxyAPIDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class CLIProxyAPISwitchDescription(SwitchEntityDescription):
    """Describes a CLIProxyAPI switch entity."""

    value_fn: Callable[[dict[str, Any]], bool]
    setter_name: str


SWITCH_DESCRIPTIONS: tuple[CLIProxyAPISwitchDescription, ...] = (
    CLIProxyAPISwitchDescription(
        key="debug",
        translation_key="debug",
        icon="mdi:bug-outline",
        value_fn=lambda data: bool(data.get("settings", {}).get("debug", False)),
        setter_name="set_debug",
    ),
    CLIProxyAPISwitchDescription(
        key="logging_to_file",
        translation_key="logging_to_file",
        icon="mdi:file-cog-outline",
        value_fn=lambda data: bool(
            data.get("settings", {}).get("logging_to_file", False)
        ),
        setter_name="set_logging_to_file",
    ),
    CLIProxyAPISwitchDescription(
        key="usage_statistics_enabled",
        translation_key="usage_statistics_enabled",
        icon="mdi:chart-box-outline",
        value_fn=lambda data: bool(
            data.get("settings", {}).get("usage_statistics_enabled", False)
        ),
        setter_name="set_usage_statistics_enabled",
    ),
    CLIProxyAPISwitchDescription(
        key="request_log",
        translation_key="request_log",
        icon="mdi:file-document-outline",
        value_fn=lambda data: bool(data.get("settings", {}).get("request_log", False)),
        setter_name="set_request_log",
    ),
    CLIProxyAPISwitchDescription(
        key="ws_auth",
        translation_key="ws_auth",
        icon="mdi:web",
        value_fn=lambda data: bool(data.get("settings", {}).get("ws_auth", False)),
        setter_name="set_ws_auth",
    ),
    CLIProxyAPISwitchDescription(
        key="switch_project",
        translation_key="switch_project",
        icon="mdi:swap-horizontal",
        value_fn=lambda data: bool(
            data.get("settings", {}).get("switch_project", False)
        ),
        setter_name="set_switch_project",
    ),
    CLIProxyAPISwitchDescription(
        key="switch_preview_model",
        translation_key="switch_preview_model",
        icon="mdi:flask-outline",
        value_fn=lambda data: bool(
            data.get("settings", {}).get("switch_preview_model", False)
        ),
        setter_name="set_switch_preview_model",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    runtime = hass.data[DOMAIN][entry.entry_id]
    coordinator: CLIProxyAPIDataUpdateCoordinator = runtime[DATA_COORDINATOR]
    api: CLIProxyAPIClient = runtime[DATA_API_CLIENT]

    async_add_entities(
        CLIProxyAPISwitch(coordinator, api, entry.entry_id, description)
        for description in SWITCH_DESCRIPTIONS
    )


class CLIProxyAPISwitch(
    CoordinatorEntity[CLIProxyAPIDataUpdateCoordinator], SwitchEntity
):
    """Representation of CLIProxyAPI switches."""

    entity_description: CLIProxyAPISwitchDescription
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: CLIProxyAPIDataUpdateCoordinator,
        api: CLIProxyAPIClient,
        entry_id: str,
        description: CLIProxyAPISwitchDescription,
    ) -> None:
        """Initialize switch."""
        super().__init__(coordinator)
        self._api = api
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        """Return switch state."""
        data = self.coordinator.data or {}
        return self.entity_description.value_fn(data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn switch on."""
        await getattr(self._api, self.entity_description.setter_name)(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn switch off."""
        await getattr(self._api, self.entity_description.setter_name)(False)
        await self.coordinator.async_request_refresh()
