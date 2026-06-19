"""Config flow for the Well Level Bridge integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback

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


def _bridge_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Return the setup/options schema."""

    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, DEFAULT_HOST)): str,
            vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
            ),
            vol.Required(
                CONF_CONNECT_ON_START,
                default=defaults.get(CONF_CONNECT_ON_START, DEFAULT_CONNECT_ON_START),
            ): bool,
            vol.Required(
                CONF_DELIMITER,
                default=defaults.get(CONF_DELIMITER, DEFAULT_DELIMITER),
            ): str,
            vol.Required(
                CONF_PRIMARY_TOKEN_INDEX,
                default=defaults.get(
                    CONF_PRIMARY_TOKEN_INDEX, DEFAULT_PRIMARY_TOKEN_INDEX
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=0)),
            vol.Required(
                CONF_FALLBACK_TOKEN_INDEX,
                default=defaults.get(
                    CONF_FALLBACK_TOKEN_INDEX, DEFAULT_FALLBACK_TOKEN_INDEX
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=0)),
            vol.Required(
                CONF_INVERT_SIGN,
                default=defaults.get(CONF_INVERT_SIGN, DEFAULT_INVERT_SIGN),
            ): bool,
            vol.Required(
                CONF_UPDATE_INTERVAL,
                default=defaults.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1)),
            vol.Required(
                CONF_WINDOW_SIZE,
                default=defaults.get(CONF_WINDOW_SIZE, DEFAULT_WINDOW_SIZE),
            ): vol.All(vol.Coerce(int), vol.Range(min=1)),
            vol.Required(
                CONF_MIN_VALUE,
                default=defaults.get(CONF_MIN_VALUE, DEFAULT_MIN_VALUE),
            ): vol.Coerce(float),
            vol.Required(
                CONF_MAX_VALUE,
                default=defaults.get(CONF_MAX_VALUE, DEFAULT_MAX_VALUE),
            ): vol.Coerce(float),
            vol.Required(
                CONF_DERIVATIVE_THRESHOLD,
                default=defaults.get(
                    CONF_DERIVATIVE_THRESHOLD, DEFAULT_DERIVATIVE_THRESHOLD
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=0)),
        }
    )


class WellLevelBridgeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Well Level Bridge."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle user setup."""

        errors: dict[str, str] = {}

        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Well Level Bridge ({user_input[CONF_HOST]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_bridge_schema(user_input or {}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> WellLevelBridgeOptionsFlow:
        """Return the options flow."""

        return WellLevelBridgeOptionsFlow(config_entry)


class WellLevelBridgeOptionsFlow(config_entries.OptionsFlow):
    """Options flow for Well Level Bridge."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""

        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle options."""

        errors: dict[str, str] = {}
        defaults = {**self._config_entry.data, **self._config_entry.options}

        if user_input is not None:
            errors = _validate(user_input)
            if not errors:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_bridge_schema(user_input or defaults),
            errors=errors,
        )


def _validate(data: dict[str, Any]) -> dict[str, str]:
    """Validate flow data."""

    errors: dict[str, str] = {}
    if not str(data[CONF_HOST]).strip():
        errors[CONF_HOST] = "host_required"
    if not str(data[CONF_DELIMITER]):
        errors[CONF_DELIMITER] = "delimiter_required"
    if float(data[CONF_MIN_VALUE]) >= float(data[CONF_MAX_VALUE]):
        errors[CONF_MIN_VALUE] = "invalid_range"
    return errors
