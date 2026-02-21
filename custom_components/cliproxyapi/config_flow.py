"""Config flow for CLIProxyAPI integration."""

from __future__ import annotations

from urllib.parse import urlparse

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig

from .api import (
    CLIProxyAPIAuthError,
    CLIProxyAPIClient,
    CLIProxyAPIConnectionError,
    CLIProxyAPIError,
    normalize_base_url,
)
from .const import (
    CONF_BASE_URL,
    CONF_ENABLE_LOG_DIAGNOSTICS,
    CONF_ENABLE_REQUEST_ERROR_LOGS,
    CONF_MANAGEMENT_KEY,
    CONF_POLL_INTERVAL_SECONDS,
    DEFAULT_BASE_URL,
    DEFAULT_ENABLE_LOG_DIAGNOSTICS,
    DEFAULT_ENABLE_REQUEST_ERROR_LOGS,
    DOMAIN,
    MAX_POLL_INTERVAL_SECONDS,
    MIN_POLL_INTERVAL_SECONDS,
    UPDATE_INTERVAL_SECONDS,
)


def _normalize_base_url(raw_value: str) -> str:
    """Normalize and validate base URL (scheme + host[:port] only)."""
    value = raw_value.strip()
    if not value:
        raise ValueError("empty base url")

    if "://" not in value:
        value = f"http://{value}"

    value = normalize_base_url(value)
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("unsupported scheme")
    if not parsed.netloc:
        raise ValueError("missing host")

    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


class CLIProxyAPIConfigFlow(ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for CLIProxyAPI."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> "CLIProxyAPIOptionsFlow":
        """Return options flow handler."""
        return CLIProxyAPIOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict | None = None):
        """Handle initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                base_url = _normalize_base_url(user_input[CONF_BASE_URL])
            except ValueError:
                errors["base"] = "invalid_url"
                base_url = ""

            management_key = user_input[CONF_MANAGEMENT_KEY].strip()

            if not errors and not management_key:
                errors["base"] = "invalid_auth"
            elif not errors:
                await self.async_set_unique_id(base_url)
                self._abort_if_unique_id_configured()

                session = async_get_clientsession(self.hass)
                client = CLIProxyAPIClient(
                    session=session,
                    base_url=base_url,
                    management_key=management_key,
                )

                try:
                    await client.async_validate_connection()
                except CLIProxyAPIAuthError:
                    errors["base"] = "invalid_auth"
                except CLIProxyAPIConnectionError:
                    errors["base"] = "cannot_connect"
                except CLIProxyAPIError:
                    errors["base"] = "cannot_connect"
                except Exception:  # pragma: no cover - defensive fallback
                    errors["base"] = "unknown"
                else:
                    return self.async_create_entry(
                        title=f"CLIProxyAPI ({base_url})",
                        data={
                            CONF_BASE_URL: base_url,
                            CONF_MANAGEMENT_KEY: management_key,
                        },
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): TextSelector(
                    TextSelectorConfig(type="url")
                ),
                vol.Required(CONF_MANAGEMENT_KEY): TextSelector(
                    TextSelectorConfig(type="password")
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class CLIProxyAPIOptionsFlow(OptionsFlow):
    """Handle options for CLIProxyAPI integration."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None):
        """Manage the options step."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_POLL_INTERVAL_SECONDS,
                    default=self._config_entry.options.get(
                        CONF_POLL_INTERVAL_SECONDS,
                        UPDATE_INTERVAL_SECONDS,
                    ),
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(
                        min=MIN_POLL_INTERVAL_SECONDS,
                        max=MAX_POLL_INTERVAL_SECONDS,
                    ),
                ),
                vol.Required(
                    CONF_ENABLE_LOG_DIAGNOSTICS,
                    default=self._config_entry.options.get(
                        CONF_ENABLE_LOG_DIAGNOSTICS,
                        DEFAULT_ENABLE_LOG_DIAGNOSTICS,
                    ),
                ): bool,
                vol.Required(
                    CONF_ENABLE_REQUEST_ERROR_LOGS,
                    default=self._config_entry.options.get(
                        CONF_ENABLE_REQUEST_ERROR_LOGS,
                        DEFAULT_ENABLE_REQUEST_ERROR_LOGS,
                    ),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
