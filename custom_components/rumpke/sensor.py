"""Sensor platform for Rumpke."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import DOMAIN, CONF_ZIP_CODE
from .coordinator import RumpkeDataCoordinator
from .utils import calculate_next_pickup

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Rumpke sensor."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RumpkeNextPickupSensor(coordinator, entry)])


class RumpkeNextPickupSensor(SensorEntity):
    """Sensor for next Rumpke pickup date."""

    def __init__(self, coordinator: RumpkeDataCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._attr_name = "Next Pickup"
        self._attr_unique_id = f"rumpke_{entry.data[CONF_ZIP_CODE]}_next_pickup"
        self._attr_icon = "mdi:trash-can"
        self._attr_has_entity_name = True

        # Create device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_ZIP_CODE])},
            name=entry.title,
            manufacturer="Rumpke Waste & Recycling",
            model="Waste & Recycling Service",
            configuration_url="https://www.rumpke.com",
        )

    @property
    def state(self):
        """Return the next pickup date."""
        next_date = self._calculate_next_pickup()
        if next_date:
            return next_date.strftime("%Y-%m-%d")
        return None

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        next_date = self._calculate_next_pickup()
        if not next_date:
            return {}

        # Use HA's timezone-aware now for days calculation
        now = dt_util.now()
        days_until = (next_date - now.date()).days

        attrs = {
            "service_day": self.coordinator.service_day,
            "zip_code": self.coordinator.zip_code,
            "days_until_pickup": days_until,
            "pickup_date": next_date.strftime("%A, %B %d, %Y"),
            "last_update": self.coordinator.data.get("last_update"),
        }

        # Add service alert info if present
        service_alert = self.coordinator.data.get("service_alert")
        if service_alert:
            attrs["service_alert"] = service_alert.get("alert_type")
            attrs["service_alert_text"] = service_alert.get("text")

        # Add county info
        if self.coordinator.data.get("county"):
            attrs["county"] = self.coordinator.data.get("county")
            attrs["state"] = self.coordinator.data.get("state")

        return attrs

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_update(self):
        """Update the sensor."""
        await self.coordinator.async_request_refresh()

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    def _calculate_next_pickup(self) -> datetime.date | None:
        """Calculate the next pickup date considering holidays."""
        if not self.coordinator.data:
            _LOGGER.warning("No coordinator data available")
            return None

        return calculate_next_pickup(
            self.coordinator.service_day,
            self.coordinator.data.get("holidays", []),
            self.coordinator.data.get("service_alert"),
        )
