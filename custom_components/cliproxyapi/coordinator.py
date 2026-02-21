"""Data coordinator for CLIProxyAPI entities."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    CLIProxyAPIAuthenticationError,
    CLIProxyAPIClient,
    CLIProxyAPIConnectionError,
    CLIProxyAPIError,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class CLIProxyAPIDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate periodic state reads from CLIProxyAPI."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: CLIProxyAPIClient,
        poll_interval_seconds: int,
        enable_log_diagnostics: bool,
        enable_request_error_logs: bool,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval_seconds),
        )
        self.api = api
        self._enable_log_diagnostics = enable_log_diagnostics
        self._enable_request_error_logs = enable_request_error_logs
        self._last_log_timestamp = 0

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch all entity data in one pass."""
        try:
            usage_raw = await self.api.get_usage()
            usage = usage_raw.get("usage", {})
            key_usage = _aggregate_key_usage(usage)
            model_token_usage = _aggregate_model_token_usage(usage)
            failed_requests = int(
                usage_raw.get("failed_requests", usage.get("failure_count", 0))
            )

            settings = {
                "debug": await self.api.get_debug(),
                "logging_to_file": await self.api.get_logging_to_file(),
                "usage_statistics_enabled": await self.api.get_usage_statistics_enabled(),
                "request_log": await self.api.get_request_log(),
                "ws_auth": await self.api.get_ws_auth(),
                "switch_project": await self.api.get_switch_project(),
                "switch_preview_model": await self.api.get_switch_preview_model(),
                "request_retry": await self.api.get_request_retry(),
                "max_retry_interval": await self.api.get_max_retry_interval(),
            }

            latest_version_raw = await self.api.get_latest_version()
            latest_version = latest_version_raw.get("latest-version")

            logs: dict[str, Any] = {
                "lines": [],
                "line-count": 0,
                "latest-timestamp": self._last_log_timestamp,
            }
            if self._enable_log_diagnostics and settings["logging_to_file"]:
                try:
                    logs = await self.api.get_logs(after=self._last_log_timestamp)
                    self._last_log_timestamp = int(
                        logs.get("latest-timestamp", self._last_log_timestamp)
                    )
                except CLIProxyAPIError as err:
                    _LOGGER.debug("Skipping logs pull due to API error: %s", err)

            request_error_logs: dict[str, Any] = {"files": []}
            if self._enable_request_error_logs:
                try:
                    request_error_logs = await self.api.get_request_error_logs()
                except CLIProxyAPIError as err:
                    _LOGGER.debug(
                        "Skipping request-error-logs pull due to API error: %s", err
                    )

            return {
                "usage": usage,
                "failed_requests": failed_requests,
                "key_usage": key_usage,
                "model_token_usage": model_token_usage,
                "settings": settings,
                "latest_version": latest_version,
                "logs": logs,
                "request_error_logs": request_error_logs.get("files", []),
                "diagnostics_enabled": {
                    "log_diagnostics": self._enable_log_diagnostics,
                    "request_error_logs": self._enable_request_error_logs,
                },
            }
        except CLIProxyAPIAuthenticationError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except CLIProxyAPIConnectionError as err:
            raise UpdateFailed(f"Connection failed: {err}") from err
        except CLIProxyAPIError as err:
            raise UpdateFailed(str(err)) from err


def _aggregate_key_usage(usage: dict[str, Any]) -> dict[str, dict[str, int]]:
    """Aggregate per-key usage from usage.apis.*.models.*.details."""
    aggregates: dict[str, dict[str, int]] = {}
    apis = usage.get("apis")
    if not isinstance(apis, dict):
        return aggregates

    for api_value in apis.values():
        if not isinstance(api_value, dict):
            continue
        models = api_value.get("models")
        if not isinstance(models, dict):
            continue

        for model_value in models.values():
            if not isinstance(model_value, dict):
                continue
            details = model_value.get("details")
            if not isinstance(details, list):
                continue

            for detail in details:
                if not isinstance(detail, dict):
                    continue
                auth_index = detail.get("auth_index")
                if not isinstance(auth_index, str) or not auth_index:
                    continue

                tokens = detail.get("tokens", {})
                total_tokens = 0
                if isinstance(tokens, dict):
                    tokens_value = tokens.get("total_tokens", 0)
                    if isinstance(tokens_value, int):
                        total_tokens = tokens_value

                entry = aggregates.setdefault(
                    auth_index,
                    {
                        "requests": 0,
                        "tokens": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "cached_tokens": 0,
                        "failed": 0,
                    },
                )
                input_tokens = 0
                output_tokens = 0
                cached_tokens = 0
                if isinstance(tokens, dict):
                    input_value = tokens.get("input_tokens", 0)
                    output_value = tokens.get("output_tokens", 0)
                    cached_value = tokens.get("cached_tokens", 0)
                    if isinstance(input_value, int):
                        input_tokens = input_value
                    if isinstance(output_value, int):
                        output_tokens = output_value
                    if isinstance(cached_value, int):
                        cached_tokens = cached_value

                entry["requests"] += 1
                entry["tokens"] += total_tokens
                entry["input_tokens"] += input_tokens
                entry["output_tokens"] += output_tokens
                entry["cached_tokens"] += cached_tokens
                if detail.get("failed") is True:
                    entry["failed"] += 1

    return aggregates


def _aggregate_model_token_usage(usage: dict[str, Any]) -> dict[str, dict[str, int]]:
    """Aggregate per-model token spend from usage.apis.*.models.*.details."""
    aggregates: dict[str, dict[str, int]] = {}
    apis = usage.get("apis")
    if not isinstance(apis, dict):
        return aggregates

    for api_value in apis.values():
        if not isinstance(api_value, dict):
            continue
        models = api_value.get("models")
        if not isinstance(models, dict):
            continue

        for model_name, model_value in models.items():
            if not isinstance(model_name, str) or not isinstance(model_value, dict):
                continue

            details = model_value.get("details")
            if not isinstance(details, list):
                continue

            entry = aggregates.setdefault(
                model_name,
                {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cached_tokens": 0,
                    "total_tokens": 0,
                    "requests": 0,
                },
            )

            for detail in details:
                if not isinstance(detail, dict):
                    continue

                tokens = detail.get("tokens")
                if not isinstance(tokens, dict):
                    continue

                input_tokens = tokens.get("input_tokens", 0)
                output_tokens = tokens.get("output_tokens", 0)
                cached_tokens = tokens.get("cached_tokens", 0)
                total_tokens = tokens.get("total_tokens", 0)

                entry["input_tokens"] += (
                    input_tokens if isinstance(input_tokens, int) else 0
                )
                entry["output_tokens"] += (
                    output_tokens if isinstance(output_tokens, int) else 0
                )
                entry["cached_tokens"] += (
                    cached_tokens if isinstance(cached_tokens, int) else 0
                )
                entry["total_tokens"] += (
                    total_tokens if isinstance(total_tokens, int) else 0
                )
                entry["requests"] += 1

    return aggregates
