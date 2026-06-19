"""Sensors for the Well Level Bridge integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .bridge import WellLevelBridge
from .const import (
    ATTR_ACCEPTED_MAX_VALUE,
    ATTR_ACCEPTED_MIN_VALUE,
    ATTR_DERIVATIVE_THRESHOLD,
    ATTR_FILTER_STAGE,
    ATTR_SAMPLE_COUNT,
    ATTR_SOURCE,
    ATTR_UPDATE_INTERVAL,
    ATTR_WINDOW_SIZE,
    DOMAIN,
)


@dataclass(frozen=True)
class WellLevelSensorDescription:
    """Description for a well-level sensor."""

    key: str
    name: str
    stage: str


SENSOR_DESCRIPTIONS: tuple[WellLevelSensorDescription, ...] = (
    WellLevelSensorDescription("raw", "Raw", "raw"),
    WellLevelSensorDescription("filtered", "Filtered", "filtered"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for one config entry."""

    bridge: WellLevelBridge = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        WellLevelSensor(entry, bridge, description)
        for description in SENSOR_DESCRIPTIONS
    )


class WellLevelSensor(SensorEntity):
    """Native well-level sensor."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.FEET
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = False
    _unsub_bridge: Callable[[], None] | None = None

    def __init__(
        self,
        entry: ConfigEntry,
        bridge: WellLevelBridge,
        description: WellLevelSensorDescription,
    ) -> None:
        """Initialize the sensor."""

        self._entry = entry
        self._bridge = bridge
        self._description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_translation_key = description.key
        self._attr_has_entity_name = True
        self._attr_name = description.name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Well Level Bridge",
            manufacturer="Custom",
        )

    @property
    def native_value(self) -> float | None:
        """Return the sensor value."""

        if self._description.key == "raw":
            return self._bridge.raw_value
        return self._bridge.filtered_value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return diagnostic attributes."""

        attrs: dict[str, Any] = {
            **self._bridge.common_attributes,
            ATTR_FILTER_STAGE: self._description.stage,
            ATTR_SOURCE: f"{self._bridge.config.host}:{self._bridge.config.port}",
            ATTR_UPDATE_INTERVAL: self._bridge.config.update_interval,
            ATTR_WINDOW_SIZE: self._bridge.config.window_size,
        }
        if self._description.key == "filtered":
            attrs.update(
                {
                    ATTR_ACCEPTED_MIN_VALUE: self._bridge.config.min_value,
                    ATTR_ACCEPTED_MAX_VALUE: self._bridge.config.max_value,
                    ATTR_DERIVATIVE_THRESHOLD: self._bridge.config.derivative_threshold,
                    ATTR_SAMPLE_COUNT: self._bridge.sample_count,
                }
            )
        return attrs

    async def async_added_to_hass(self) -> None:
        """Register bridge listener."""

        self._unsub_bridge = self._bridge.async_add_listener(
            self._handle_bridge_update
        )

    async def async_will_remove_from_hass(self) -> None:
        """Remove bridge listener."""

        if self._unsub_bridge is not None:
            self._unsub_bridge()
            self._unsub_bridge = None

    @callback
    def _handle_bridge_update(self) -> None:
        """Handle a bridge update."""

        self.async_write_ha_state()
