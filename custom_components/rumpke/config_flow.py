"""Config flow for Rumpke Waste Collection."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_ZIP_CODE, CONF_SERVICE_DAY
from .api import RumpkeApiClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ZIP_CODE): cv.string,
        vol.Required(CONF_SERVICE_DAY): vol.In(
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    api = RumpkeApiClient(session)

    # Verify the zip code is in Rumpke's service area
    region_data = await api.get_region(data[CONF_ZIP_CODE])

    if not region_data or "region" not in region_data:
        raise ValueError("Zip code not in Rumpke service area")

    return {
        "title": f"Rumpke - {region_data['region']}",
        "region": region_data["region"],
    }


class RumpkeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Rumpke."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except ValueError:
                errors["base"] = "invalid_zip"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if already configured
                await self.async_set_unique_id(user_input[CONF_ZIP_CODE])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
