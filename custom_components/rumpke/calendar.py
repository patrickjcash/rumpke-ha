"""Calendar platform for Rumpke."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, CONF_ZIP_CODE
from .coordinator import RumpkeDataCoordinator
from .utils import calculate_next_pickup, generate_pickup_dates

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Rumpke calendar."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RumpkePickupCalendar(coordinator, entry)])


class RumpkePickupCalendar(CalendarEntity):
    """Calendar entity for Rumpke pickup dates."""

    def __init__(self, coordinator: RumpkeDataCoordinator, entry: ConfigEntry) -> None:
        """Initialize the calendar."""
        self.coordinator = coordinator
        self._attr_name = "Pickup Schedule"
        self._attr_unique_id = f"rumpke_{entry.data[CONF_ZIP_CODE]}_calendar"
        self._attr_has_entity_name = True

        # Link to same device as sensor
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.data[CONF_ZIP_CODE])},
            name=entry.title,
            manufacturer="Rumpke Waste & Recycling",
            model="Waste & Recycling Service",
            configuration_url="https://www.rumpke.com",
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return current/next event (determines calendar state)."""
        if not self.coordinator.data:
            return None

        # Get next pickup date
        next_date = calculate_next_pickup(
            self.coordinator.service_day,
            self.coordinator.data.get("holidays", []),
            self.coordinator.data.get("service_alert"),
        )

        if next_date:
            return CalendarEvent(
                summary="Rumpke Pickup",
                start=next_date,
                end=next_date + timedelta(days=1),
                uid=f"rumpke_{next_date.isoformat()}_{self.coordinator.zip_code}",
            )
        return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date, end_date
    ) -> list[CalendarEvent]:
        """Return calendar events within date range."""
        if not self.coordinator.data:
            return []

        # Never generate events before today
        from homeassistant.util import dt as dt_util
        today = dt_util.now().date()
        effective_start = max(start_date.date(), today)

        # Limit to 3 months of events (90 days)
        max_end_date = effective_start + timedelta(days=90)
        limited_end_date = min(end_date.date(), max_end_date)

        # Generate all pickup dates in the range
        pickup_dates = generate_pickup_dates(
            self.coordinator.service_day,
            self.coordinator.data.get("holidays", []),
            self.coordinator.data.get("service_alert"),
            effective_start,
            limited_end_date,
        )

        # Convert to CalendarEvent objects
        events = []
        for pickup_date in pickup_dates:
            events.append(
                CalendarEvent(
                    summary="Rumpke Pickup",
                    start=pickup_date,
                    end=pickup_date + timedelta(days=1),
                    uid=f"rumpke_{pickup_date.isoformat()}_{self.coordinator.zip_code}",
                    description=f"Service day: {self.coordinator.service_day}",
                )
            )

        return events

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
