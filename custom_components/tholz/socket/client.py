import socket
import json
import logging

_LOGGER = logging.getLogger(__name__)


def _recv_json(sock):
    """Acumula pacotes até formar um JSON completo (a resposta pode vir fragmentada)."""
    buf = b""
    while True:
        chunk = sock.recv(8192)
        if not chunk:
            break
        buf += chunk
        try:
            return json.loads(buf.decode())
        except ValueError:
            continue
    return json.loads(buf.decode())


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
                decoded = _recv_json(s)

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
                decoded = _recv_json(s)

                self.last_data = decoded.get("response")
                _LOGGER.debug("[set_status] data: %s", self.last_data)
                return self.last_data
        except Exception as e:
            _LOGGER.warning("[set_status] error: %s", e)
            return False
