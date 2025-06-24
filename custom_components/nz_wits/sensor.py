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
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    SCHEDULE_RTD,
    SCHEDULE_INTERIM,
    SCHEDULE_PRSS,
    SCHEDULE_PRSL,
    SCHEDULE_TYPES,
    CONF_UPDATE_RTD,
    CONF_UPDATE_INTERIM,
    CONF_UPDATE_PRSS,
    CONF_UPDATE_PRSL,
    CONF_NODE,
)
from .coordinator import WitsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    # Get the coordinator from hass
    coordinator: WitsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get options for which sensors to create
    update_options = {
        SCHEDULE_RTD: entry.options.get(CONF_UPDATE_RTD, True),
        SCHEDULE_INTERIM: entry.options.get(CONF_UPDATE_INTERIM, True),
        SCHEDULE_PRSS: entry.options.get(CONF_UPDATE_PRSS, True),
        SCHEDULE_PRSL: entry.options.get(CONF_UPDATE_PRSL, True),
    }

    entities = []
    # Create a sensor for each schedule type that is enabled in options
    for schedule_type, details in SCHEDULE_TYPES.items():
        if update_options.get(schedule_type, False): # Default to False if somehow not in options
            entities.append(
                WitsPriceSensor(coordinator, entry, schedule_type, details["name"])
            )
        
    async_add_entities(entities)


class WitsPriceSensor(CoordinatorEntity[WitsDataUpdateCoordinator], SensorEntity):
    """Representation of a WITS Spot Price Sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_suggested_display_precision = None
    _attr_state_class = SensorStateClass.TOTAL
    
    # The API gives price per MWh, we want price per kWh
    _attr_native_unit_of_measurement = f"NZD/{UnitOfEnergy.KILO_WATT_HOUR}"

    def __init__(
        self,
        coordinator: WitsDataUpdateCoordinator,
        config_entry: ConfigEntry,
        schedule_type: str,
        schedule_name: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._schedule_type = schedule_type
        self._node = config_entry.data.get(CONF_NODE, "Unknown Node")

        # Unique ID for the sensor
        # Ensure unique_id is present on the config_entry
        config_entry_unique_id = config_entry.unique_id or f"fallback_unique_id_{config_entry.entry_id}"
        self._attr_unique_id = f"{config_entry_unique_id}_{self._schedule_type}"
        
        # Name of the sensor
        self._attr_name = f"{schedule_name}" # The device name will provide context

        # Device Info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry_unique_id)},
            name=f"WITS ({self._node})",
            manufacturer="NZ WITS Data Service",
            model=f"Node {self._node}",
            configuration_url=f"https://www.electricityinfo.co.nz/historic?node={self._node}",
        )

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data or self._schedule_type not in self.coordinator.data:
            return None
        
        schedule_data = self.coordinator.data[self._schedule_type]
        if not schedule_data or not isinstance(schedule_data, list) or len(schedule_data) == 0:
            return None

        # Assuming the first item in the list is the current/most relevant price
        price_data = schedule_data[0]
        price_mwh = price_data.get("price")

        if price_mwh is None:
            return None
        
        try:
            return round(float(price_mwh) / 1000, 5) # Convert MWh to kWh
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Could not parse price '%s' for %s schedule for node %s",
                price_mwh,
                self._schedule_type,
                self._node
            )
            return None

    @property
    def extra_state_attributes(self) -> dict[str, any] | None:
        """Return the state attributes."""
        if not self.coordinator.data or self._schedule_type not in self.coordinator.data:
            return None
            
        schedule_data = self.coordinator.data[self._schedule_type]
        if not schedule_data or not isinstance(schedule_data, list) or len(schedule_data) == 0:
            return None

        current_data_point = schedule_data[0]
        
        attributes = {
            "node": current_data_point.get("node"),
            "schedule_type": self._schedule_type, # Use the internal schedule type key
            "schedule_name": SCHEDULE_TYPES[self._schedule_type]["name"], # Get human-readable name
            "trading_period": current_data_point.get("tradingPeriod"),
            "trading_datetime": current_data_point.get("tradingDateTime"),
            "last_updated_from_coordinator": (
                dt_util.as_local(self.coordinator.data["last_api_success_utc"]).isoformat()
                if self.coordinator.data and "last_api_success_utc" in self.coordinator.data and self.coordinator.data["last_api_success_utc"]
                else None
            ),
        }
        
        # For forecast schedules, add the full forecast list
        if self._schedule_type in [SCHEDULE_PRSS, SCHEDULE_PRSL]:
            attributes["forecast_data"] = schedule_data
            
        return attributes

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Available if the coordinator has data and this specific schedule's data is present
        return (
            super().available
            and self.coordinator.data is not None
            and self._schedule_type in self.coordinator.data
            and self.coordinator.data[self._schedule_type] is not None
        )
