"""Sensor entities for CLIProxyAPI diagnostics and usage."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import CLIProxyAPIDataUpdateCoordinator
from .entity import CLIProxyAPIEntity


def _timestamp_or_none(data: dict[str, Any]) -> datetime | None:
    """Convert latest-timestamp integer to timezone-aware datetime."""
    timestamp = int(data.get("logs", {}).get("latest-timestamp", 0) or 0)
    if timestamp <= 0:
        return None
    return datetime.fromtimestamp(timestamp, tz=UTC)


def _error_rate(data: dict[str, Any]) -> float:
    """Calculate percentage of failed requests."""
    usage = data.get("usage", {})
    total = usage.get("total_requests", 0)
    failures = usage.get("failure_count", 0)
    if not isinstance(total, int) or total <= 0:
        return 0.0
    if not isinstance(failures, int):
        return 0.0
    return round((failures / total) * 100, 2)


def _diag_enabled(data: dict[str, Any], key: str) -> bool:
    """Read diagnostics feature flags from coordinator payload."""
    settings = data.get("diagnostics_enabled", {})
    return bool(settings.get(key, False))


def _sanitize_unique_fragment(raw: str) -> str:
    """Create stable unique-id fragments from auth index values."""
    sanitized = re.sub(r"[^a-zA-Z0-9_]+", "_", raw).strip("_").lower()
    return sanitized or "unknown"


@dataclass(frozen=True, kw_only=True)
class CLIProxyAPISensorDescription(SensorEntityDescription):
    """Describes a CLIProxyAPI sensor entity."""

    value_fn: Callable[[dict[str, Any]], StateType]
    available_fn: Callable[[dict[str, Any]], bool] | None = None


SENSOR_DESCRIPTIONS: tuple[CLIProxyAPISensorDescription, ...] = (
    CLIProxyAPISensorDescription(
        key="total_requests",
        translation_key="total_requests",
        icon="mdi:counter",
        native_unit_of_measurement="requests",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("usage", {}).get("total_requests", 0),
    ),
    CLIProxyAPISensorDescription(
        key="success_count",
        translation_key="success_count",
        icon="mdi:check-circle-outline",
        native_unit_of_measurement="requests",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("usage", {}).get("success_count", 0),
    ),
    CLIProxyAPISensorDescription(
        key="failure_count",
        translation_key="failure_count",
        icon="mdi:alert-outline",
        native_unit_of_measurement="requests",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("usage", {}).get("failure_count", 0),
    ),
    CLIProxyAPISensorDescription(
        key="failed_requests",
        translation_key="failed_requests",
        icon="mdi:alert-circle-outline",
        native_unit_of_measurement="requests",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("failed_requests", 0),
    ),
    CLIProxyAPISensorDescription(
        key="error_rate",
        translation_key="error_rate",
        icon="mdi:chart-donut",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_error_rate,
    ),
    CLIProxyAPISensorDescription(
        key="total_tokens",
        translation_key="total_tokens",
        icon="mdi:database-outline",
        native_unit_of_measurement="tokens",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("usage", {}).get("total_tokens", 0),
    ),
    CLIProxyAPISensorDescription(
        key="latest_version",
        translation_key="latest_version",
        icon="mdi:tag-outline",
        value_fn=lambda data: data.get("latest_version"),
    ),
    CLIProxyAPISensorDescription(
        key="key_usage_entries",
        translation_key="key_usage_entries",
        icon="mdi:key-chain-variant",
        native_unit_of_measurement="keys",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.get("key_usage", {})),
    ),
    CLIProxyAPISensorDescription(
        key="log_line_count",
        translation_key="log_line_count",
        icon="mdi:file-document-outline",
        native_unit_of_measurement="lines",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("logs", {}).get("line-count", 0),
        available_fn=lambda data: _diag_enabled(data, "log_diagnostics"),
    ),
    CLIProxyAPISensorDescription(
        key="latest_log_timestamp",
        translation_key="latest_log_timestamp",
        icon="mdi:clock-outline",
        device_class="timestamp",
        value_fn=_timestamp_or_none,
        available_fn=lambda data: _diag_enabled(data, "log_diagnostics"),
    ),
    CLIProxyAPISensorDescription(
        key="request_error_log_files",
        translation_key="request_error_log_files",
        icon="mdi:file-alert-outline",
        native_unit_of_measurement="files",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.get("request_error_logs", [])),
        available_fn=lambda data: _diag_enabled(data, "request_error_logs"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    coordinator: CLIProxyAPIDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    async_add_entities(
        CLIProxyAPISensor(entry, coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )

    created_key_sensors: set[str] = set()

    @callback
    def _async_add_missing_key_sensors() -> None:
        payload = coordinator.data or {}
        key_usage = payload.get("key_usage", {})
        if not isinstance(key_usage, dict):
            return

        new_entities: list[CLIProxyAPIKeyUsageSensor] = []
        for key_id in key_usage:
            if not isinstance(key_id, str) or key_id in created_key_sensors:
                continue
            created_key_sensors.add(key_id)
            new_entities.append(CLIProxyAPIKeyUsageSensor(entry, coordinator, key_id))

        if new_entities:
            async_add_entities(new_entities)

    _async_add_missing_key_sensors()
    entry.async_on_unload(
        coordinator.async_add_listener(_async_add_missing_key_sensors)
    )


class CLIProxyAPISensor(CLIProxyAPIEntity, SensorEntity):
    """Representation of CLIProxyAPI sensor entities."""

    entity_description: CLIProxyAPISensorDescription
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: CLIProxyAPIDataUpdateCoordinator,
        description: CLIProxyAPISensorDescription,
    ) -> None:
        """Initialize sensor entity."""
        super().__init__(entry, coordinator, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        """Return entity availability."""
        if not super().available:
            return False
        if self.entity_description.available_fn is None:
            return True
        return bool(self.entity_description.available_fn(self.coordinator.data or {}))

    @property
    def native_value(self) -> StateType:
        """Return native sensor value."""
        data = self.coordinator.data or {}
        return self.entity_description.value_fn(data)


class CLIProxyAPIKeyUsageSensor(CLIProxyAPIEntity, SensorEntity):
    """Per-key usage sensor derived from usage details auth_index data."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:key-chain-variant"
    _attr_native_unit_of_measurement = "requests"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: CLIProxyAPIDataUpdateCoordinator,
        key_id: str,
    ) -> None:
        """Initialize per-key usage sensor."""
        key_fragment = _sanitize_unique_fragment(key_id)
        super().__init__(entry, coordinator, f"key_usage_{key_fragment}_requests")
        self._key_id = key_id
        self._attr_name = f"Key {key_id[:8]} requests"

    @property
    def native_value(self) -> StateType:
        """Return request count for this key."""
        data = self.coordinator.data or {}
        usage = data.get("key_usage", {})
        if not isinstance(usage, dict):
            return 0
        key_data = usage.get(self._key_id, {})
        if not isinstance(key_data, dict):
            return 0
        value = key_data.get("requests", 0)
        return int(value) if isinstance(value, int) else 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extended usage metrics for this key."""
        data = self.coordinator.data or {}
        usage = data.get("key_usage", {})
        key_data = usage.get(self._key_id, {}) if isinstance(usage, dict) else {}

        requests = int(key_data.get("requests", 0)) if isinstance(key_data, dict) else 0
        failed = int(key_data.get("failed", 0)) if isinstance(key_data, dict) else 0
        tokens = int(key_data.get("tokens", 0)) if isinstance(key_data, dict) else 0
        return {
            "auth_index": self._key_id,
            "tokens": tokens,
            "failed_requests": failed,
            "success_requests": max(requests - failed, 0),
        }
