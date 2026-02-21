"""Async API client for CLIProxyAPI Management API."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientSession

from .const import (
    API_BASE_PATH,
    ENDPOINT_DEBUG,
    ENDPOINT_LATEST_VERSION,
    ENDPOINT_LOGGING_TO_FILE,
    ENDPOINT_LOGS,
    ENDPOINT_MAX_RETRY_INTERVAL,
    ENDPOINT_REQUEST_ERROR_LOGS,
    ENDPOINT_REQUEST_LOG,
    ENDPOINT_REQUEST_RETRY,
    ENDPOINT_SWITCH_PREVIEW_MODEL,
    ENDPOINT_SWITCH_PROJECT,
    ENDPOINT_USAGE,
    ENDPOINT_USAGE_STATISTICS_ENABLED,
    ENDPOINT_WS_AUTH,
    REQUEST_TIMEOUT_SECONDS,
)


class CLIProxyAPIError(Exception):
    """Base exception for CLIProxyAPI errors."""


class CLIProxyAPIConnectionError(CLIProxyAPIError):
    """Raised when the API is unreachable."""


class CLIProxyAPIAuthenticationError(CLIProxyAPIError):
    """Raised when management credentials are invalid."""


# Backward-compatible alias used by earlier scaffolding.
CLIProxyAPIAuthError = CLIProxyAPIAuthenticationError


class CLIProxyAPIRequestError(CLIProxyAPIError):
    """Raised when API requests fail with a non-auth error."""

    def __init__(self, status: int, message: str) -> None:
        """Initialize request error."""
        super().__init__(f"Request failed ({status}): {message}")
        self.status = status
        self.message = message


class CLIProxyAPIClient:
    """HTTP client for safe CLIProxyAPI management endpoints."""

    def __init__(
        self,
        session: ClientSession,
        base_url: str,
        management_key: str,
    ) -> None:
        """Initialize API client."""
        self._session = session
        self._base_url = normalize_base_url(base_url)
        self._management_key = management_key

    def _url(self, endpoint: str) -> str:
        """Build full API URL for endpoint."""
        return f"{self._base_url}{API_BASE_PATH}{endpoint}"

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        payload: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        expected_statuses: set[int] | None = None,
    ) -> dict[str, Any]:
        """Execute a management API request and return parsed JSON."""
        statuses = expected_statuses or {200}
        headers = {
            "Authorization": f"Bearer {self._management_key}",
            "X-Management-Key": self._management_key,
            "Content-Type": "application/json",
        }

        try:
            async with self._session.request(
                method,
                self._url(endpoint),
                headers=headers,
                json=payload,
                params=params,
                timeout=REQUEST_TIMEOUT_SECONDS,
            ) as response:
                response_data = await self._safe_json(response)
                if response.status in statuses:
                    return response_data

                message = (
                    response_data.get("error")
                    or response_data.get("message")
                    or "unknown"
                )
                if response.status in (401, 403):
                    raise CLIProxyAPIAuthenticationError(message)
                raise CLIProxyAPIRequestError(response.status, message)
        except ClientError as err:
            raise CLIProxyAPIConnectionError(str(err)) from err

    async def _safe_json(self, response: Any) -> dict[str, Any]:
        """Read response as JSON when possible, else wrap plain text."""
        try:
            data = await response.json(content_type=None)
        except ValueError:
            text = await response.text()
            return {"message": text} if text else {}

        return data if isinstance(data, dict) else {"data": data}

    async def validate(self) -> None:
        """Validate that the API can be reached with the provided key."""
        await self.get_debug()

    async def async_validate_connection(self) -> None:
        """Compatibility shim for config flow validation call sites."""
        await self.validate()

    async def get_usage(self) -> dict[str, Any]:
        """Fetch usage statistics snapshot."""
        return await self._request("GET", ENDPOINT_USAGE)

    async def get_latest_version(self) -> dict[str, Any]:
        """Fetch latest upstream release version."""
        return await self._request("GET", ENDPOINT_LATEST_VERSION)

    async def get_debug(self) -> bool:
        """Return debug toggle state."""
        payload = await self._request("GET", ENDPOINT_DEBUG)
        return bool(payload.get("debug", False))

    async def set_debug(self, value: bool) -> None:
        """Set debug toggle state."""
        await self._request("PATCH", ENDPOINT_DEBUG, payload={"value": value})

    async def get_logging_to_file(self) -> bool:
        """Return logging-to-file state."""
        payload = await self._request("GET", ENDPOINT_LOGGING_TO_FILE)
        return bool(payload.get("logging-to-file", False))

    async def set_logging_to_file(self, value: bool) -> None:
        """Set logging-to-file state."""
        await self._request("PATCH", ENDPOINT_LOGGING_TO_FILE, payload={"value": value})

    async def get_usage_statistics_enabled(self) -> bool:
        """Return usage-statistics-enabled state."""
        payload = await self._request("GET", ENDPOINT_USAGE_STATISTICS_ENABLED)
        return bool(payload.get("usage-statistics-enabled", False))

    async def set_usage_statistics_enabled(self, value: bool) -> None:
        """Set usage-statistics-enabled state."""
        await self._request(
            "PATCH", ENDPOINT_USAGE_STATISTICS_ENABLED, payload={"value": value}
        )

    async def get_request_log(self) -> bool:
        """Return request-log state."""
        payload = await self._request("GET", ENDPOINT_REQUEST_LOG)
        return bool(payload.get("request-log", False))

    async def set_request_log(self, value: bool) -> None:
        """Set request-log state."""
        await self._request("PATCH", ENDPOINT_REQUEST_LOG, payload={"value": value})

    async def get_ws_auth(self) -> bool:
        """Return ws-auth state."""
        payload = await self._request("GET", ENDPOINT_WS_AUTH)
        return bool(payload.get("ws-auth", False))

    async def set_ws_auth(self, value: bool) -> None:
        """Set ws-auth state."""
        await self._request("PATCH", ENDPOINT_WS_AUTH, payload={"value": value})

    async def get_switch_project(self) -> bool:
        """Return quota-exceeded switch-project state."""
        payload = await self._request("GET", ENDPOINT_SWITCH_PROJECT)
        return bool(payload.get("switch-project", False))

    async def set_switch_project(self, value: bool) -> None:
        """Set quota-exceeded switch-project state."""
        await self._request("PATCH", ENDPOINT_SWITCH_PROJECT, payload={"value": value})

    async def get_switch_preview_model(self) -> bool:
        """Return quota-exceeded switch-preview-model state."""
        payload = await self._request("GET", ENDPOINT_SWITCH_PREVIEW_MODEL)
        return bool(payload.get("switch-preview-model", False))

    async def set_switch_preview_model(self, value: bool) -> None:
        """Set quota-exceeded switch-preview-model state."""
        await self._request(
            "PATCH", ENDPOINT_SWITCH_PREVIEW_MODEL, payload={"value": value}
        )

    async def get_request_retry(self) -> int:
        """Return request retry count."""
        payload = await self._request("GET", ENDPOINT_REQUEST_RETRY)
        return int(payload.get("request-retry", 0))

    async def set_request_retry(self, value: int) -> None:
        """Set request retry count."""
        await self._request("PATCH", ENDPOINT_REQUEST_RETRY, payload={"value": value})

    async def get_max_retry_interval(self) -> int:
        """Return max retry interval in seconds."""
        payload = await self._request("GET", ENDPOINT_MAX_RETRY_INTERVAL)
        return int(payload.get("max-retry-interval", 0))

    async def set_max_retry_interval(self, value: int) -> None:
        """Set max retry interval in seconds."""
        await self._request(
            "PATCH", ENDPOINT_MAX_RETRY_INTERVAL, payload={"value": value}
        )

    async def get_logs(self, after: int = 0) -> dict[str, Any]:
        """Fetch latest logs. Uses incremental polling via 'after'."""
        return await self._request("GET", ENDPOINT_LOGS, params={"after": after})

    async def clear_logs(self) -> dict[str, Any]:
        """Clear current and rotated logs."""
        return await self._request("DELETE", ENDPOINT_LOGS)

    async def get_request_error_logs(self) -> dict[str, Any]:
        """Fetch request-error-log file list."""
        return await self._request("GET", ENDPOINT_REQUEST_ERROR_LOGS)


def normalize_base_url(value: str) -> str:
    """Normalize base URL and drop management path if user pasted it."""
    base_url = value.strip().rstrip("/")
    if base_url.endswith(API_BASE_PATH):
        return base_url[: -len(API_BASE_PATH)]
    return base_url
