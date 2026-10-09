import asyncio
import logging
from copy import deepcopy
from time import monotonic

from homeassistant.exceptions import HomeAssistantError

from ..entities.heating.utils import get_heating_sensor_type
from .client import TholzSocketClient

_LOGGER = logging.getLogger(__name__)


class TholzSocketClientManager:
    def __init__(self, client: TholzSocketClient, polling_interval: int):
        self._client = client
        self._polling_interval = polling_interval
        self._data = None
        self._read_data = None
        self._last_attempt = None
        self._last_successful_read = None
        self._lock = asyncio.Lock()
        self._task = None

    def start(self, hass):
        if self._task is None:
            self._task = hass.loop.create_task(self._updater())

    async def stop(self):
        """
        Cancel the polling task.

        Without this the task outlives the config entry, so reloading or
        removing the integration leaves an extra poller running against the
        controller for the lifetime of the process.
        """
        if self._task is None:
            return

        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    @property
    def last_successful_read(self):
        """Monotonic completion time of the last structurally valid device read."""
        return self._last_successful_read

    @property
    def is_fresh(self):
        """Allow three polling intervals plus five seconds for I/O/publication."""
        return (
            self._read_data is not None
            and self._last_successful_read is not None
            and monotonic() - self._last_successful_read
            <= 3 * self._polling_interval + 5
        )

    async def _fetch_data(self):
        self._last_attempt = monotonic()
        try:
            data = await asyncio.to_thread(self._client.get_status)
        except Exception:
            self._data = None
            self._read_data = None
            _LOGGER.exception("unexpected error while reading the controller")
            return
        if not self._valid_snapshot(data):
            self._data = None
            self._read_data = None
            return
        self._data = deepcopy(data)
        self._read_data = deepcopy(data)
        self._last_successful_read = monotonic()

    @staticmethod
    def _valid_snapshot(data):
        """Reject empty/ACK payloads and malformed native heating containers."""
        if not isinstance(data, dict) or not data:
            return False
        sections = ("heating", "heatings", "light", "leds", "outputs", "monitors")
        if not any(data.get(key) for key in ("id", *sections)):
            return False
        if "id" in data and (
            isinstance(data["id"], bool) or not isinstance(data["id"], int)
        ):
            return False
        if any(key in data and not isinstance(data[key], dict) for key in sections):
            return False
        heatings = list(data.get("heatings", {}).values())
        if "heating" in data:
            heatings.append(data["heating"])
        return all(get_heating_sensor_type(state) is not None for state in heatings)

    async def _updater(self):
        while True:
            try:
                async with self._lock:
                    await self._fetch_data()
            except asyncio.CancelledError:
                raise
            except Exception:
                # Keep polling. An unhandled error here would end the task and
                # silently stop every update until Home Assistant restarts.
                _LOGGER.exception("unexpected error while polling the controller")

            await asyncio.sleep(self._polling_interval)

    async def get_status(self):
        """Synchronize command/setup state with any in-flight device poll."""
        async with self._lock:
            if self._data is None or not self.is_fresh:
                await self._fetch_data()
            if not self.is_fresh:
                message = "Controller unavailable"
                raise HomeAssistantError(message)
            # Legacy entities share command state; sensors use a separate copy.
            return self._data

    async def get_sensor_status(self):
        """Return only fresh native reads, without waiting or retrying I/O."""
        return deepcopy(self._read_data) if self.is_fresh else None

    async def set_status(self, payload):
        async with self._lock:
            result = await asyncio.to_thread(self._client.set_status, payload)
            # Preserve consecutive command state, never sensor read proof.
            if result and isinstance(result, dict):
                self._data = deepcopy(result)
            return result
