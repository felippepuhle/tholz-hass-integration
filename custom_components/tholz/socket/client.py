import json
import logging
import socket
import time

_LOGGER = logging.getLogger(__name__)

# The controller accepts a limited number of concurrent connections. Beyond that
# it completes the TCP handshake and sends nothing back, so an empty reply means
# "busy, try again" rather than "invalid request".
RETRIES = 3
RETRY_DELAY = 1.5
TIMEOUT = 3


class TholzSocketClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.last_data = None

    def _receive(self, s):
        """Read one JSON object.

        The controller does not close the connection after replying, so reading
        until EOF blocks. Stop as soon as the outermost object is closed, and
        fall back to whatever arrived if the socket times out first.
        """
        buffer = bytearray()
        depth = 0
        started = False

        while True:
            try:
                chunk = s.recv(4096)
            except socket.timeout:
                break
            if not chunk:
                break

            buffer.extend(chunk)
            for byte in chunk:
                if byte == 0x7B:  # {
                    depth += 1
                    started = True
                elif byte == 0x7D:  # }
                    depth -= 1
            if started and depth <= 0:
                break

        return bytes(buffer)

    def _request(self, msg):
        with socket.create_connection((self.host, self.port), timeout=TIMEOUT) as s:
            s.settimeout(TIMEOUT)
            s.sendall(json.dumps(msg).encode())
            raw = self._receive(s)

        if not raw:
            raise ConnectionError("empty reply (controller busy)")

        return json.loads(raw.decode()).get("response")

    def _request_with_retry(self, msg, label):
        last_error = None

        for attempt in range(1, RETRIES + 1):
            try:
                data = self._request(msg)
            except Exception as e:  # noqa: BLE001
                last_error = e
                _LOGGER.debug("[%s] attempt %s/%s failed: %s", label, attempt, RETRIES, e)
                if attempt < RETRIES:
                    time.sleep(RETRY_DELAY)
                continue

            self.last_data = data
            _LOGGER.debug("[%s] data: %s", label, data)
            return data

        _LOGGER.warning("[%s] no reply after %s attempts: %s", label, RETRIES, last_error)
        return None

    def get_status(self):
        return self._request_with_retry({"command": "getDevice"}, "get_status")

    def set_status(self, payload):
        result = self._request_with_retry(
            {"command": "setDevice", "argument": payload}, "set_status"
        )
        return result if result is not None else False
