import asyncio
import logging
from datetime import datetime

from .client import TholzSocketClient

_LOGGER = logging.getLogger(__name__)


class TholzSocketClientManager:
    def __init__(self, client: TholzSocketClient, polling_interval: int):
        self._client = client
        self._polling_interval = polling_interval
        self._data = None
        self._last_update = None
        self._lock = asyncio.Lock()
        self._task = None

    def start(self, hass):
        if self._task is None:
            self._task = hass.loop.create_task(self._updater())

    async def stop(self):
        """Cancel the polling task.

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

    async def _fetch_data(self):
        self._data = await asyncio.to_thread(self._client.get_status)
        self._last_update = datetime.now()

    async def _updater(self):
        while True:
            try:
                async with self._lock:
                    await self._fetch_data()
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001
                # Keep polling. An unhandled error here would end the task and
                # silently stop every update until Home Assistant restarts.
                _LOGGER.exception("unexpected error while polling the controller")

            await asyncio.sleep(self._polling_interval)

    async def get_status(self):
        async with self._lock:
            if self._data is None:
                await self._fetch_data()
            return self._data

    async def set_status(self, payload):
        async with self._lock:
            result = await asyncio.to_thread(self._client.set_status, payload)
            if result and isinstance(result, dict):
                self._data = result
                self._last_update = datetime.now()
            return result
