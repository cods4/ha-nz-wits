"""Constants for the NZ WITS Spot Price integration."""

DOMAIN = "nz_wits"

# API Configuration
API_BASE_URL = "https://api.electricityinfo.co.nz"
TOKEN_URL = f"{API_BASE_URL}/login/oauth2/token"
PRICES_URL = f"{API_BASE_URL}/api/market-prices/v1/prices"

# Configuration keys
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_NODE = "node"

# Default values
DEFAULT_NODE = "TGA0331"

# Sensor schedules
SCHEDULE_RTD = "RTD"
SCHEDULE_INTERIM = "Interim"
SCHEDULE_PRSS = "PRSS"
SCHEDULE_PRSL = "PRSL"

SCHEDULE_TYPES = {
    SCHEDULE_RTD: {
        "name": "Real Time Dispatch (RTD)",
        "params": {"schedules": SCHEDULE_RTD, "marketType": "E", "offset": 0},
    },
    SCHEDULE_INTERIM: {
        "name": "Interim Price",
        "params": {"schedules": "Interim", "marketType": "E", "back": 3, "offset": 0},
    },
    SCHEDULE_PRSS: {
        "name": "Price Responsive Schedule Short (PRSS)",
        "params": {"schedules": SCHEDULE_PRSS, "marketType": "E", "forward": 6, "offset": 0},
    },
    SCHEDULE_PRSL: {
        "name": "Price Responsive Schedule Long (PRSL)",
        "params": {"schedules": SCHEDULE_PRSL, "marketType": "E", "forward": 48, "offset": 0},
    },
}
