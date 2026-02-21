"""Constants for the CLIProxyAPI integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "cliproxyapi"

CONF_BASE_URL = "base_url"
CONF_MANAGEMENT_KEY = "management_key"
CONF_POLL_INTERVAL_SECONDS = "poll_interval_seconds"
CONF_ENABLE_LOG_DIAGNOSTICS = "enable_log_diagnostics"
CONF_ENABLE_REQUEST_ERROR_LOGS = "enable_request_error_logs"

DEFAULT_BASE_URL = "http://127.0.0.1:8317"
API_BASE_PATH = "/v0/management"

UPDATE_INTERVAL_SECONDS = 30
REQUEST_TIMEOUT_SECONDS = 15
MIN_POLL_INTERVAL_SECONDS = 5
MAX_POLL_INTERVAL_SECONDS = 300

DEFAULT_ENABLE_LOG_DIAGNOSTICS = False
DEFAULT_ENABLE_REQUEST_ERROR_LOGS = False

DATA_API_CLIENT = "api_client"
DATA_COORDINATOR = "coordinator"

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.BUTTON,
]


ENDPOINT_USAGE = "/usage"
ENDPOINT_LATEST_VERSION = "/latest-version"

ENDPOINT_DEBUG = "/debug"
ENDPOINT_LOGGING_TO_FILE = "/logging-to-file"
ENDPOINT_USAGE_STATISTICS_ENABLED = "/usage-statistics-enabled"
ENDPOINT_REQUEST_LOG = "/request-log"
ENDPOINT_WS_AUTH = "/ws-auth"
ENDPOINT_SWITCH_PROJECT = "/quota-exceeded/switch-project"
ENDPOINT_SWITCH_PREVIEW_MODEL = "/quota-exceeded/switch-preview-model"

ENDPOINT_REQUEST_RETRY = "/request-retry"
ENDPOINT_MAX_RETRY_INTERVAL = "/max-retry-interval"

ENDPOINT_LOGS = "/logs"
ENDPOINT_REQUEST_ERROR_LOGS = "/request-error-logs"
