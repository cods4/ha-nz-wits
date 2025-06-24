"""API Client for NZ WITS Spot Price."""
import asyncio
import logging
from typing import Any

import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    TOKEN_URL,
    PRICES_URL,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_NODE,
    SCHEDULE_TYPES,
)

_LOGGER = logging.getLogger(__name__)


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""

class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""


class WitsApiClient:
    """Handles all communication with the WITS API."""

    def __init__(self, config: dict[str, Any], session: aiohttp.ClientSession | None = None):
        """Initialize the API client."""
        self._client_id = config[CONF_CLIENT_ID]
        self._client_secret = config[CONF_CLIENT_SECRET]
        self.node = config[CONF_NODE]
        self._session = session
        self._access_token = None
        self._lock = asyncio.Lock()

    async def _get_access_token(self) -> str:
        """Get a new access token using client credentials."""
        if self._session is None:
            raise CannotConnect("Session not initialized")
            
        _LOGGER.debug("Requesting new access token")
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        try:
            async with self._session.post(TOKEN_URL, headers=headers, data=data, timeout=10) as response:
                if response.status == 401 or response.status == 400:
                    raise InvalidAuth("Authentication failed")
                response.raise_for_status()
                token_data = await response.json()
                self._access_token = token_data["access_token"]
                _LOGGER.info("Successfully obtained new access token")
                return self._access_token
        except asyncio.TimeoutError as exc:
            raise CannotConnect("Timeout connecting to API") from exc
        except aiohttp.ClientError as exc:
            raise CannotConnect(f"Error connecting to API: {exc}") from exc

    async def _request(self, method: str, url: str, params: dict | None = None) -> Any:
        """Make an authenticated request to the API."""
        async with self._lock:
            if self._access_token is None:
                await self._get_access_token()

        if self._session is None:
            raise CannotConnect("Session not initialized")

        headers = {"Authorization": f"Bearer {self._access_token}"}
        
        try:
            return await self._perform_request(method, url, headers, params)
        except InvalidAuth:
            _LOGGER.info("Access token expired or invalid, requesting a new one")
            async with self._lock:
                await self._get_access_token() # Force a refresh
            # Retry the request with the new token
            headers = {"Authorization": f"Bearer {self._access_token}"}
            return await self._perform_request(method, url, headers, params)

    async def _perform_request(self, method, url, headers, params):
        """Helper to perform the actual HTTP request."""
        try:
            async with self._session.request(method, url, headers=headers, params=params, timeout=15) as response:
                if response.status == 401:
                    raise InvalidAuth("Token is invalid")
                response.raise_for_status()
                return await response.json()
        except asyncio.TimeoutError as exc:
            raise CannotConnect("Timeout during API request") from exc
        except aiohttp.ClientError as exc:
            raise CannotConnect(f"Error during API request: {exc}") from exc

    async def test_authentication(self):
        """Test if we can authenticate with the API."""
        await self._get_access_token()

    async def get_price_data(self, schedule_type: str) -> list[dict[str, Any]]:
        """Fetch price data for a given schedule."""
        if schedule_type not in SCHEDULE_TYPES:
            _LOGGER.error("Unknown schedule type: %s", schedule_type)
            return []

        params = SCHEDULE_TYPES[schedule_type]["params"].copy()
        params["nodes"] = self.node
        
        _LOGGER.debug("Fetching price data for schedule '%s' with params: %s", schedule_type, params)
        data = await self._request("GET", PRICES_URL, params=params)

        if not data or not isinstance(data, list) or "prices" not in data[0]:
            _LOGGER.warning("Received empty or malformed price data for %s", schedule_type)
            return []
        
        return data[0]["prices"]
