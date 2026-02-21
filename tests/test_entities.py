"""Entity model tests for CLIProxyAPI integration."""

from __future__ import annotations

import pytest

pytest.importorskip("homeassistant")

from custom_components.cliproxyapi.button import BUTTON_DESCRIPTIONS
from custom_components.cliproxyapi.number import NUMBER_DESCRIPTIONS
from custom_components.cliproxyapi.sensor import SENSOR_DESCRIPTIONS
from custom_components.cliproxyapi.switch import SWITCH_DESCRIPTIONS


def _assert_unique_keys(descriptions) -> None:
    keys = [description.key for description in descriptions]
    assert len(keys) == len(set(keys))


def test_sensor_description_keys_are_unique() -> None:
    """Sensor entities have stable, non-duplicated keys."""
    _assert_unique_keys(SENSOR_DESCRIPTIONS)


def test_switch_description_keys_are_unique() -> None:
    """Switch entities have stable, non-duplicated keys."""
    _assert_unique_keys(SWITCH_DESCRIPTIONS)


def test_number_description_keys_are_unique() -> None:
    """Number entities have stable, non-duplicated keys."""
    _assert_unique_keys(NUMBER_DESCRIPTIONS)


def test_button_description_keys_are_unique() -> None:
    """Button entities have stable, non-duplicated keys."""
    _assert_unique_keys(BUTTON_DESCRIPTIONS)


def test_no_forbidden_entity_keys_exposed() -> None:
    """Ensure constrained feature classes are not exposed as entities."""
    forbidden_terms = {"auth", "oauth", "api_keys", "port", "management_key"}

    all_keys = {
        *(description.key for description in SENSOR_DESCRIPTIONS),
        *(description.key for description in SWITCH_DESCRIPTIONS),
        *(description.key for description in NUMBER_DESCRIPTIONS),
        *(description.key for description in BUTTON_DESCRIPTIONS),
    }

    assert all(not any(term in key for term in forbidden_terms) for key in all_keys)
