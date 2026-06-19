"""Runtime bridge for the Well Level Bridge integration."""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import logging
import re
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_CONNECTED,
    ATTR_LAST_ERROR,
    ATTR_LAST_FRAME,
    ATTR_REJECT_REASON,
    DEFAULT_CONNECT_ON_START,
    DEFAULT_DELIMITER,
    DEFAULT_DERIVATIVE_THRESHOLD,
    DEFAULT_HOST,
    DEFAULT_INVERT_SIGN,
    DEFAULT_MAX_VALUE,
    DEFAULT_MIN_VALUE,
    DEFAULT_PORT,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_WINDOW_SIZE,
)

_LOGGER = logging.getLogger(__name__)
_VALUE_BEFORE_FT = re.compile(r"([-+]?(?:\d+(?:\.\d*)?|\.\d+))\s*ft\b", re.IGNORECASE)

FrameCallback = Callable[[], None]


@dataclass(frozen=True)
class BridgeConfig:
    """Runtime configuration."""

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    delimiter: str = DEFAULT_DELIMITER
    invert_sign: bool = DEFAULT_INVERT_SIGN
    connect_on_start: bool = DEFAULT_CONNECT_ON_START
    window_size: int = DEFAULT_WINDOW_SIZE
    update_interval: float = DEFAULT_UPDATE_INTERVAL
    min_value: float = DEFAULT_MIN_VALUE
    max_value: float = DEFAULT_MAX_VALUE
    derivative_threshold: float = DEFAULT_DERIVATIVE_THRESHOLD


class WellLevelBridge:
    """Read a TCP serial stream and maintain raw/filtered well-level values."""

    def __init__(self, hass: HomeAssistant, config: BridgeConfig) -> None:
        """Initialize the bridge."""

        self.hass = hass
        self.config = config
        self.raw_value: float | None = None
        self.filtered_value: float | None = None
        self.last_raw_update: datetime | None = None
        self.last_filtered_update: datetime | None = None
        self.last_frame: str | None = None
        self.last_error: str | None = None
        self.last_reject_reason: str | None = None
        self.connected = False

        self._values: deque[float] = deque(maxlen=max(1, config.window_size))
        self._interval_values: list[float] = []
        self._last_filtered_candidate: float | None = None
        self._last_raw_emit = 0.0
        self._listeners: set[FrameCallback] = set()
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connect_unsub: Callable[[], None] | None = None

    async def async_start(self) -> None:
        """Start the bridge if enabled."""

        if not self.config.connect_on_start:
            _LOGGER.info(
                "Well Level Bridge is configured but not connecting because "
                "connect_on_start is disabled"
            )
            return

        self._stop_event.clear()
        self._task = self.hass.loop.create_task(self._run())

    async def async_stop(self) -> None:
        """Stop the bridge."""

        if self._connect_unsub is not None:
            self._connect_unsub()
            self._connect_unsub = None

        self._stop_event.set()
        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        self.connected = False
        self._notify_listeners()

    @callback
    def async_add_listener(self, listener: FrameCallback) -> Callable[[], None]:
        """Register a listener for sensor state updates."""

        self._listeners.add(listener)

        def remove_listener() -> None:
            self._listeners.discard(listener)

        return remove_listener

    @property
    def sample_count(self) -> int:
        """Return the current moving-average sample count."""

        return len(self._values)

    @property
    def common_attributes(self) -> dict[str, Any]:
        """Return attributes shared by raw and filtered sensors."""

        return {
            ATTR_CONNECTED: self.connected,
            ATTR_LAST_ERROR: self.last_error,
            ATTR_LAST_FRAME: self.last_frame,
            ATTR_REJECT_REASON: self.last_reject_reason,
        }

    async def _run(self) -> None:
        """Keep the TCP stream connected until stopped."""

        while not self._stop_event.is_set():
            try:
                await self._read_forever()
            except asyncio.CancelledError:
                raise
            except Exception as err:
                self.connected = False
                self.last_error = str(err)
                self._notify_listeners()
                _LOGGER.warning(
                    "Well Level Bridge connection to %s:%s failed: %s",
                    self.config.host,
                    self.config.port,
                    err,
                )

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=10)
            except TimeoutError:
                pass

    async def _read_forever(self) -> None:
        """Connect and process framed stream data."""

        reader, writer = await asyncio.open_connection(self.config.host, self.config.port)
        self._writer = writer
        self.connected = True
        self.last_error = None
        self._notify_listeners()
        buffer = ""

        try:
            while not self._stop_event.is_set():
                data = await reader.read(1024)
                if not data:
                    raise ConnectionError("connection closed")

                buffer += data.decode("utf-8", errors="ignore")
                while self.config.delimiter in buffer:
                    frame, buffer = buffer.split(self.config.delimiter, 1)
                    self._process_frame(frame)
        finally:
            self.connected = False
            writer.close()
            await writer.wait_closed()
            if self._writer is writer:
                self._writer = None
            self._notify_listeners()

    @callback
    def _process_frame(self, frame: str) -> None:
        """Process one incoming frame."""

        self.last_frame = frame.strip()
        parsed_value = self._parse_frame(frame)
        if parsed_value is None:
            self.last_reject_reason = "unparsable_frame"
            self._notify_listeners()
            return

        raw_value = -parsed_value if self.config.invert_sign else parsed_value
        self._interval_values.append(raw_value)
        loop_now = self.hass.loop.time()
        should_emit = (
            self._last_raw_emit == 0.0
            or loop_now - self._last_raw_emit >= self.config.update_interval
        )
        if not should_emit:
            self.last_reject_reason = None
            self._notify_listeners()
            return

        now = dt_util.utcnow()
        interval_average = round(
            sum(self._interval_values) / len(self._interval_values), 2
        )
        self._interval_values.clear()
        self._last_raw_emit = loop_now
        self.raw_value = interval_average
        self.last_raw_update = now
        self._values.append(interval_average)
        moving_average = round(sum(self._values) / len(self._values), 2)

        if not self.config.min_value <= moving_average <= self.config.max_value:
            self.last_reject_reason = "outside_accepted_range"
            self._notify_listeners()
            return

        if self._last_filtered_candidate is not None:
            delta = abs(moving_average - self._last_filtered_candidate)
            if delta > self.config.derivative_threshold:
                self.last_reject_reason = "delta_too_high"
                self._notify_listeners()
                return

        self._last_filtered_candidate = moving_average
        self.filtered_value = moving_average
        self.last_filtered_update = now
        self.last_reject_reason = None
        self._notify_listeners()

    def _parse_frame(self, frame: str) -> float | None:
        """Parse the well-level value from an incoming text frame."""

        unit_match = _VALUE_BEFORE_FT.search(frame)
        if unit_match is not None:
            try:
                return float(unit_match.group(1))
            except ValueError:
                pass
        return None

    @callback
    def _notify_listeners(self) -> None:
        """Notify registered HA entities."""

        for listener in list(self._listeners):
            listener()
