"""Constants for the Well Level Bridge integration."""

from __future__ import annotations

DOMAIN = "well_level_bridge"

DEFAULT_HOST = "192.168.10.4"
DEFAULT_PORT = 9001
DEFAULT_DELIMITER = ">>"
DEFAULT_PRIMARY_TOKEN_INDEX = 6
DEFAULT_FALLBACK_TOKEN_INDEX = 7
DEFAULT_INVERT_SIGN = True
DEFAULT_CONNECT_ON_START = False
DEFAULT_WINDOW_SIZE = 200
DEFAULT_UPDATE_INTERVAL = 5.0
DEFAULT_MIN_VALUE = -250.0
DEFAULT_MAX_VALUE = -60.0
DEFAULT_DERIVATIVE_THRESHOLD = 5.0

CONF_CONNECT_ON_START = "connect_on_start"
CONF_DELIMITER = "delimiter"
CONF_DERIVATIVE_THRESHOLD = "derivative_threshold"
CONF_FALLBACK_TOKEN_INDEX = "fallback_token_index"
CONF_INVERT_SIGN = "invert_sign"
CONF_MAX_VALUE = "max_value"
CONF_MIN_VALUE = "min_value"
CONF_PRIMARY_TOKEN_INDEX = "primary_token_index"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_WINDOW_SIZE = "window_size"

ATTR_ACCEPTED_MAX_VALUE = "accepted_max_value"
ATTR_ACCEPTED_MIN_VALUE = "accepted_min_value"
ATTR_CONNECTED = "connected"
ATTR_DERIVATIVE_THRESHOLD = "derivative_threshold"
ATTR_FILTER_STAGE = "filter_stage"
ATTR_LAST_ERROR = "last_error"
ATTR_LAST_FRAME = "last_frame"
ATTR_REJECT_REASON = "last_reject_reason"
ATTR_SAMPLE_COUNT = "sample_count"
ATTR_SOURCE = "source"
ATTR_UPDATE_INTERVAL = "update_interval"
ATTR_WINDOW_SIZE = "window_size"

