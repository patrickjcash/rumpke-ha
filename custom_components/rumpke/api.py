"""API client for Rumpke."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from bs4 import BeautifulSoup

try:
    from .const import API_BASE_URL, API_GET_REGION, REGION_SCHEDULE_MAP, SERVICE_ALERTS_URL
except ImportError:
    from const import API_BASE_URL, API_GET_REGION, REGION_SCHEDULE_MAP, SERVICE_ALERTS_URL

_LOGGER = logging.getLogger(__name__)


class RumpkeApiClient:
    """API client for Rumpke waste collection."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self.session = session

    async def get_region(self, zip_code: str) -> dict[str, Any] | None:
        """Get region information for a zip code."""
        url = f"{API_BASE_URL}{API_GET_REGION}"
        params = {"zipCode": zip_code}

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.debug("Region data for %s: %s", zip_code, data)
                    return data
                else:
                    _LOGGER.error("Failed to get region: HTTP %s", response.status)
                    return None
        except Exception as e:
            _LOGGER.error("Error getting region for zip %s: %s", zip_code, e)
            return None

    async def get_holiday_schedule_html(self, zip_code: str) -> str | None:
        """Get holiday schedule HTML for a zip code."""
        # First get the region to determine the correct schedule page
        region_data = await self.get_region(zip_code)
        if not region_data or "region" not in region_data:
            _LOGGER.error("Could not determine region for zip %s", zip_code)
            return None

        region = region_data["region"]
        schedule_path = REGION_SCHEDULE_MAP.get(region)

        if not schedule_path:
            _LOGGER.error("No schedule path found for region %s", region)
            return None

        url = f"{API_BASE_URL}{schedule_path}"
        params = {"zip": zip_code}

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    html = await response.text()
                    _LOGGER.debug("Retrieved holiday schedule for region %s", region)
                    return html
                else:
                    _LOGGER.error("Failed to get holiday schedule: HTTP %s", response.status)
                    return None
        except Exception as e:
            _LOGGER.error("Error getting holiday schedule: %s", e)
            return None

    async def get_service_alerts_html(self) -> str | None:
        """Get service alerts HTML."""
        try:
            async with self.session.get(SERVICE_ALERTS_URL) as response:
                if response.status == 200:
                    html = await response.text()
                    _LOGGER.debug("Retrieved service alerts")
                    return html
                else:
                    _LOGGER.error("Failed to get service alerts: HTTP %s", response.status)
                    return None
        except Exception as e:
            _LOGGER.error("Error getting service alerts: %s", e)
            return None
