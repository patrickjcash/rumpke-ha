"""Data coordinator for Rumpke."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import aiohttp

from .api import RumpkeApiClient
from .parser import HolidayScheduleParser
from .alerts_parser import ServiceAlertsParser
from .utils import get_county_from_zip
from .const import SCAN_INTERVAL_HOURS

_LOGGER = logging.getLogger(__name__)


class RumpkeDataCoordinator(DataUpdateCoordinator):
    """Data coordinator for Rumpke waste collection."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        zip_code: str,
        service_day: str,
    ) -> None:
        """Initialize the coordinator."""
        self.api = RumpkeApiClient(session)
        self.zip_code = zip_code
        self.service_day = service_day

        # Get county information for service alerts
        county_info = get_county_from_zip(zip_code)
        if county_info:
            self.county, self.state = county_info
            _LOGGER.info("Zip %s -> %s County, %s", zip_code, self.county, self.state)
        else:
            self.county = None
            self.state = None
            _LOGGER.warning("Could not determine county for zip %s", zip_code)

        super().__init__(
            hass,
            _LOGGER,
            name="Rumpke Waste & Recycling",
            update_interval=timedelta(hours=SCAN_INTERVAL_HOURS),
        )

    async def _async_update_data(self):
        """Fetch data from Rumpke."""
        try:
            # Get holiday schedule
            html = await self.api.get_holiday_schedule_html(self.zip_code)
            if not html:
                raise UpdateFailed("Failed to fetch holiday schedule")

            holidays = HolidayScheduleParser.parse(html)
            _LOGGER.debug("Parsed %d holidays", len(holidays))

            # Get service alerts
            service_alert = None
            if self.county and self.state:
                _LOGGER.debug("Fetching service alerts for %s County, %s", self.county, self.state)
                alerts_html = await self.api.get_service_alerts_html()
                if alerts_html:
                    service_alert = ServiceAlertsParser.parse(alerts_html, self.county, self.state)
                    if service_alert:
                        _LOGGER.info(
                            "Service alert for %s County, %s: %s (delay: %s days)",
                            self.county,
                            self.state,
                            service_alert.get("alert_type"),
                            service_alert.get("delay_days", 0),
                        )
                    else:
                        _LOGGER.debug("No service alerts found for %s County, %s", self.county, self.state)
                else:
                    _LOGGER.warning("Failed to fetch service alerts HTML")
            else:
                _LOGGER.warning("County/state not available, cannot fetch service alerts")

            return {
                "holidays": holidays,
                "service_alert": service_alert,
                "county": self.county,
                "state": self.state,
                "last_update": datetime.now(),
            }

        except Exception as err:
            raise UpdateFailed(f"Error fetching Rumpke data: {err}")
