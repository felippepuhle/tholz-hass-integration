from datetime import timedelta

DOMAIN = "tholz"

CONF_NAME_KEY = "name"
CONF_HOST_KEY = "host"
CONF_PORT_KEY = "port"
CONF_PORT_DEFAULT_VALUE = 4000
CONF_POLLING_INTERVAL_KEY = "polling_interval"
CONF_POLLING_INTERVAL_DEFAULT_VALUE = 5

ENTITIES_SCAN_INTERVAL = timedelta(seconds=1)
