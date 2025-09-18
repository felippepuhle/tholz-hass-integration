import socket
import json
import logging

_LOGGER = logging.getLogger(__name__)


class TholzSocketClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.last_data = None

    def get_status(self):
        try:
            with socket.create_connection((self.host, self.port), timeout=3) as s:
                msg = {"command": "getDevice"}
                _LOGGER.debug("[get_status] call: %s", msg)

                s.sendall(json.dumps(msg).encode())
                data = s.recv(8192)
                decoded = json.loads(data.decode())

                self.last_data = decoded.get("response")
                _LOGGER.debug("[get_status] data: %s", self.last_data)
                return self.last_data
        except Exception as e:
            _LOGGER.warning("[get_status] error: %s", e)
            return None

    def set_status(self, payload):
        try:
            with socket.create_connection((self.host, self.port), timeout=3) as s:
                msg = {"command": "setDevice", "argument": payload}
                _LOGGER.debug("[set_status] call: %s", msg)

                s.sendall(json.dumps(msg).encode())
                data = s.recv(8192)
                decoded = json.loads(data.decode())

                self.last_data = decoded.get("response")
                _LOGGER.debug("[set_status] data: %s", self.last_data)
                return self.last_data
        except Exception as e:
            _LOGGER.warning("[set_status] error: %s", e)
            return False
