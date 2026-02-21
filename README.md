# CLIProxyAPI Home Assistant Integration (HACS)

Custom Home Assistant integration to monitor and control selected CLIProxyAPI Management API runtime settings.

## Scope and Safety

This integration intentionally **does not** implement:

- management key change workflows
- port changing workflows
- provider key configuration (`/api-keys`, provider key arrays)
- auth-file / login / OAuth / vertex flows

Supported controls are limited to safe runtime toggles and numeric retry settings.

## Features

- Connectivity and usage sensors (`/usage`, `/latest-version`)
- Per-key usage aggregation (derived from `usage.apis.*.models.*.details[].auth_index`)
- Runtime switches:
  - debug
  - logging to file
  - usage statistics enabled
  - request log
  - ws auth
  - quota exceeded: switch project / switch preview model
- Runtime numbers:
  - request retry
  - max retry interval
- Buttons:
  - refresh data
  - clear logs (disabled by default)
- Optional diagnostics collection:
  - logs endpoint polling
  - request-error-log file list polling

## Configuration

After installing via HACS and restarting Home Assistant:

1. Add integration: **CLIProxyAPI**
2. Enter:
   - `Base URL` (example: `http://127.0.0.1:8317`)
   - `Management key`

### Options

Open integration **Configure** to set:

- `Polling interval (seconds)` (5 to 300)
- `Enable log diagnostics` (default: off)
- `Enable request error log diagnostics` (default: off)

## Per-Key Usage Component

The integration builds per-key usage metrics from `auth_index` in usage details.

- Creates a summary sensor: `Tracked key usage entries`
- Creates one diagnostic sensor per discovered key with request count as state
- Per-key sensor attributes include:
  - `auth_index`
  - `tokens`
  - `failed_requests`
  - `success_requests`

## Lovelace Usage Card

An example card is included at `USAGE_CARD.yaml`.

Use Raw Configuration Editor in Lovelace and paste the YAML, then adjust entity IDs if your names differ.

For destructive actions like log clearing, use a confirmation action in dashboard buttons.

## Lovelace Full View

A full dashboard view template is included at `USAGE_VIEW.yaml`.

How to use:

1. Open your dashboard in edit mode.
2. Use Raw Configuration Editor.
3. Under `views:`, paste the `USAGE_VIEW.yaml` content as a new view item.
4. Save and adjust any entity IDs that differ in your instance.

The view includes a dedicated **Per-Key Usage** section and optional diagnostics cards.
It also includes an auto-populated per-key list using `custom:auto-entities`.

## Lovelace Mobile View

A compact mobile-focused view template is included at `USAGE_VIEW_MOBILE.yaml`.

How to use:

1. Open your dashboard in edit mode.
2. Use Raw Configuration Editor.
3. Under `views:`, paste the `USAGE_VIEW_MOBILE.yaml` content as a new view item.
4. Save and adjust entity IDs if needed.

The mobile view includes quick health tiles, compact controls, and a confirmation-protected clear logs button.

## Auto-Entities Requirement

`USAGE_VIEW.yaml` and `USAGE_VIEW_MOBILE.yaml` include `custom:auto-entities` cards to auto-list per-key usage sensors.

Install **Auto Entities** via HACS (Lovelace plugin):

- Repository: `thomasloven/lovelace-auto-entities`

If you do not want to install it, remove the `type: custom:auto-entities` cards and keep the static entities cards.

## Development

Local checks used in this repository:

```bash
python3 -m compileall custom_components/cliproxyapi tests
python3 -m pytest -q
```

Note: tests are currently guarded with `pytest.importorskip("homeassistant")` in environments where Home Assistant is not installed.
