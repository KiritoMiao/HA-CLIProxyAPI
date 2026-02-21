"""Button entities for CLIProxyAPI one-shot actions."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import CLIProxyAPIClient
from .const import DATA_API_CLIENT, DATA_COORDINATOR, DOMAIN
from .coordinator import CLIProxyAPIDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class CLIProxyAPIButtonDescription(ButtonEntityDescription):
    """Describes a CLIProxyAPI button entity."""

    action: str


BUTTON_DESCRIPTIONS: tuple[CLIProxyAPIButtonDescription, ...] = (
    CLIProxyAPIButtonDescription(
        key="clear_logs",
        translation_key="clear_logs",
        icon="mdi:delete-sweep-outline",
        action="clear_logs",
        entity_registry_enabled_default=False,
    ),
    CLIProxyAPIButtonDescription(
        key="refresh",
        translation_key="refresh",
        icon="mdi:refresh",
        entity_category=EntityCategory.DIAGNOSTIC,
        action="refresh_data",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    runtime = hass.data[DOMAIN][entry.entry_id]
    coordinator: CLIProxyAPIDataUpdateCoordinator = runtime[DATA_COORDINATOR]
    api: CLIProxyAPIClient = runtime[DATA_API_CLIENT]

    async_add_entities(
        CLIProxyAPIButton(coordinator, api, entry.entry_id, description)
        for description in BUTTON_DESCRIPTIONS
    )


class CLIProxyAPIButton(
    CoordinatorEntity[CLIProxyAPIDataUpdateCoordinator], ButtonEntity
):
    """Representation of CLIProxyAPI actions."""

    entity_description: CLIProxyAPIButtonDescription
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: CLIProxyAPIDataUpdateCoordinator,
        api: CLIProxyAPIClient,
        entry_id: str,
        description: CLIProxyAPIButtonDescription,
    ) -> None:
        """Initialize button entity."""
        super().__init__(coordinator)
        self._api = api
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    async def async_press(self) -> None:
        """Execute button action."""
        if self.entity_description.action == "clear_logs":
            await self._api.clear_logs()
        await self.coordinator.async_request_refresh()
