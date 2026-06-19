"""Well Level Bridge integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .bridge import BridgeConfig, WellLevelBridge
from .const import (
    CONF_CONNECT_ON_START,
    CONF_DELIMITER,
    CONF_DERIVATIVE_THRESHOLD,
    CONF_FALLBACK_TOKEN_INDEX,
    CONF_INVERT_SIGN,
    CONF_MAX_VALUE,
    CONF_MIN_VALUE,
    CONF_PRIMARY_TOKEN_INDEX,
    CONF_UPDATE_INTERVAL,
    CONF_WINDOW_SIZE,
    DEFAULT_CONNECT_ON_START,
    DEFAULT_DELIMITER,
    DEFAULT_DERIVATIVE_THRESHOLD,
    DEFAULT_FALLBACK_TOKEN_INDEX,
    DEFAULT_HOST,
    DEFAULT_INVERT_SIGN,
    DEFAULT_MAX_VALUE,
    DEFAULT_MIN_VALUE,
    DEFAULT_PORT,
    DEFAULT_PRIMARY_TOKEN_INDEX,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_WINDOW_SIZE,
    DOMAIN,
)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Well Level Bridge from a config entry."""

    bridge = WellLevelBridge(hass, _config_from_entry(entry))
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = bridge

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await bridge.async_start()
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    bridge: WellLevelBridge | None = hass.data.get(DOMAIN, {}).pop(
        entry.entry_id, None
    )
    if bridge is not None:
        await bridge.async_stop()
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload after options change."""

    await hass.config_entries.async_reload(entry.entry_id)


def _config_from_entry(entry: ConfigEntry) -> BridgeConfig:
    """Build runtime configuration from entry data and options."""

    data: dict[str, Any] = {**entry.data, **entry.options}
    return BridgeConfig(
        host=str(data.get(CONF_HOST, DEFAULT_HOST)).strip(),
        port=int(data.get(CONF_PORT, DEFAULT_PORT)),
        delimiter=str(data.get(CONF_DELIMITER, DEFAULT_DELIMITER)),
        primary_token_index=int(
            data.get(CONF_PRIMARY_TOKEN_INDEX, DEFAULT_PRIMARY_TOKEN_INDEX)
        ),
        fallback_token_index=int(
            data.get(CONF_FALLBACK_TOKEN_INDEX, DEFAULT_FALLBACK_TOKEN_INDEX)
        ),
        invert_sign=bool(data.get(CONF_INVERT_SIGN, DEFAULT_INVERT_SIGN)),
        connect_on_start=bool(
            data.get(CONF_CONNECT_ON_START, DEFAULT_CONNECT_ON_START)
        ),
        window_size=int(data.get(CONF_WINDOW_SIZE, DEFAULT_WINDOW_SIZE)),
        update_interval=float(data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)),
        min_value=float(data.get(CONF_MIN_VALUE, DEFAULT_MIN_VALUE)),
        max_value=float(data.get(CONF_MAX_VALUE, DEFAULT_MAX_VALUE)),
        derivative_threshold=float(
            data.get(CONF_DERIVATIVE_THRESHOLD, DEFAULT_DERIVATIVE_THRESHOLD)
        ),
    )
