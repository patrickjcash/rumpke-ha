"""Sensor platform for Rumpke."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_ZIP_CODE, CONF_SERVICE_DAY
from .coordinator import RumpkeDataCoordinator

_LOGGER = logging.getLogger(__name__)

# Day name to weekday number mapping
DAYS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Rumpke sensor."""
    zip_code = entry.data[CONF_ZIP_CODE]
    service_day = entry.data[CONF_SERVICE_DAY]

    session = async_get_clientsession(hass)
    coordinator = RumpkeDataCoordinator(hass, session, zip_code, service_day)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([RumpkeNextPickupSensor(coordinator, entry)])


class RumpkeNextPickupSensor(SensorEntity):
    """Sensor for next Rumpke pickup date."""

    def __init__(self, coordinator: RumpkeDataCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._attr_name = "Rumpke Next Pickup"
        self._attr_unique_id = f"rumpke_{entry.data[CONF_ZIP_CODE]}_next_pickup"
        self._attr_icon = "mdi:trash-can"

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

        days_until = (next_date - datetime.now().date()).days

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
            return None

        today = datetime.now().date()
        service_weekday = DAYS.get(self.coordinator.service_day)

        if service_weekday is None:
            _LOGGER.error("Invalid service day: %s", self.coordinator.service_day)
            return None

        # Find the next occurrence of the service day (including today)
        days_ahead = service_weekday - today.weekday()
        if days_ahead < 0:  # Target day already happened this week (but not today)
            days_ahead += 7

        next_pickup = today + timedelta(days=days_ahead)

        # Apply service alert delays first
        service_alert = self.coordinator.data.get("service_alert")
        if service_alert and service_alert.get("has_delay"):
            delay_days = service_alert.get("delay_days", 0)
            if delay_days > 0:
                next_pickup += timedelta(days=delay_days)
                _LOGGER.debug(
                    "Applied service alert delay of %d day(s), new date: %s",
                    delay_days,
                    next_pickup,
                )

        # Then apply holiday delays
        holidays = self.coordinator.data.get("holidays", [])
        next_pickup = self._apply_holiday_delays(next_pickup, holidays)

        return next_pickup

    def _apply_holiday_delays(self, pickup_date: datetime.date, holidays: list) -> datetime.date:
        """Apply holiday delays to the pickup date."""
        # Check for holidays in the week of the pickup
        week_start = pickup_date - timedelta(days=pickup_date.weekday())
        week_end = week_start + timedelta(days=6)

        for holiday in holidays:
            if not holiday.get("has_delay") or not holiday.get("date"):
                continue

            holiday_date = holiday["date"]

            # If holiday is in the same week and before/on pickup day
            if week_start <= holiday_date <= week_end and holiday_date <= pickup_date:
                # Delay by one day
                pickup_date += timedelta(days=1)
                _LOGGER.debug(
                    "Pickup delayed by %s on %s, new date: %s",
                    holiday["name"],
                    holiday_date,
                    pickup_date,
                )

        return pickup_date
