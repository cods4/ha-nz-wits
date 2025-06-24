"""Sensor platform for NZ WITS Spot Price."""
from __future__ import annotations

import logging
from datetime import timedelta, datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .api import WitsApiClient, CannotConnect, InvalidAuth
from .const import DOMAIN, SCHEDULE_RTD, SCHEDULE_INTERIM, SCHEDULE_PRSS, SCHEDULE_PRSL, SCHEDULE_TYPES

_LOGGER = logging.getLogger(__name__)

# Define update intervals for each schedule type
SCAN_INTERVALS = {
    SCHEDULE_RTD: timedelta(minutes=1),
    SCHEDULE_INTERIM: timedelta(minutes=5),
    SCHEDULE_PRSS: timedelta(minutes=60),
    SCHEDULE_PRSL: timedelta(minutes=60),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    api_client: WitsApiClient = hass.data[DOMAIN][entry.entry_id]

    entities = []
    # Create a coordinator and sensor for each schedule type
    for schedule_type, details in SCHEDULE_TYPES.items():
        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{schedule_type}",
            update_method=lambda st=schedule_type: api_client.get_price_data(st),
            update_interval=SCAN_INTERVALS[schedule_type],
        )
        # Fetch initial data
        await coordinator.async_config_entry_first_refresh()
        
        entities.append(
            WitsPriceSensor(coordinator, entry, api_client, schedule_type, details["name"])
        )
        
    async_add_entities(entities)


class WitsPriceSensor(CoordinatorEntity, SensorEntity):
    """Representation of a WITS Spot Price Sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.MONETARY
    # The 'state_class' is intentionally omitted here.
    # For 'monetary' device_class, 'state_class' should not be 'measurement'.
    # Home Assistant will handle it correctly without it being explicitly set.
    
    # The API gives price per MWh, we want price per kWh
    _attr_native_unit_of_measurement = f"NZD/{UnitOfEnergy.KILO_WATT_HOUR}"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        config_entry: ConfigEntry,
        api_client: WitsApiClient,
        schedule_type: str,
        schedule_name: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._api_client = api_client
        self._schedule_type = schedule_type

        # Unique ID for the sensor
        self._attr_unique_id = f"{config_entry.unique_id}_{schedule_type}"
        
        # Name of the sensor
        self.entity_id = f"sensor.{DOMAIN}_{api_client.node.lower()}_{schedule_type.lower()}"
        self._attr_name = f"Spot Price {schedule_name}"

        # Link to the device
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._config_entry.unique_id)},
            "name": f"WITS API Node {self._api_client.node}",
            "manufacturer": "NZ WITS",
            "model": self._api_client.node,
            "entry_type": "service",
        }

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        # The first price in the list is the current/next price
        price_mwh = self.coordinator.data[0].get("price")
        if price_mwh is None:
            return None
        
        # Convert price from $/MWh to $/kWh
        return round(float(price_mwh) / 1000, 5)

    @property
    def extra_state_attributes(self) -> dict[str, any] | None:
        """Return the state attributes."""
        if not self.coordinator.data:
            return None
            
        # The first item is the primary data point
        current_data = self.coordinator.data[0]
        
        attributes = {
            "node": current_data.get("node"),
            "schedule": current_data.get("schedule"),
            "trading_period": current_data.get("tradingPeriod"),
            "trading_datetime": current_data.get("tradingDateTime"),
            "last_updated": self.coordinator.last_update_success_time,
        }
        
        # For forecast schedules, add the full forecast as an attribute
        if self._schedule_type in [SCHEDULE_PRSS, SCHEDULE_PRSL]:
            attributes["forecast"] = self.coordinator.data
            
        return attributes
