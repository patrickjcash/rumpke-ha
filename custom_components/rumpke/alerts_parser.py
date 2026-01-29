"""Parser for Rumpke service alerts."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)


class ServiceAlertsParser:
    """Parser for Rumpke service alerts HTML."""

    @staticmethod
    def parse(html: str, county: str, state: str) -> dict[str, Any] | None:
        """
        Parse service alerts for a specific county.

        Args:
            html: Service alerts page HTML
            county: County name (e.g., "Delaware")
            state: State abbreviation (e.g., "OH")

        Returns:
            Alert data dict or None if no alert for this county
        """
        soup = BeautifulSoup(html, "html.parser")

        # Find the state section
        state_map = {"OH": "Ohio", "KY": "Kentucky", "IN": "Indiana", "WV": "West Virginia", "IL": "Illinois"}
        state_name = state_map.get(state)

        if not state_name:
            _LOGGER.warning("Unknown state: %s", state)
            return None

        # Look for accordion sections with county data
        accordion = soup.find_all("div", class_="repeatable-content")

        for section in accordion:
            # Check if this section contains the state name
            heading = section.find_previous("h3")
            if not heading or state_name.lower() not in heading.get_text().lower():
                continue

            # Found the right state section, now look for the county
            list_items = section.find_all("li")

            for item in list_items:
                text = item.get_text(strip=True)

                # Check if this is our county
                if text.lower().startswith(f"{county.lower()}:"):
                    _LOGGER.debug("Found alert for %s County, %s: %s", county, state, text)

                    # Parse the alert details
                    alert = ServiceAlertsParser._parse_alert_text(text)
                    return alert

        _LOGGER.debug("No service alert found for %s County, %s", county, state)
        return None

    @staticmethod
    def _parse_alert_text(text: str) -> dict[str, Any]:
        """Parse alert text to extract delay information."""
        text_lower = text.lower()

        # Check for delay patterns
        has_delay = False
        delay_days = 0
        alert_type = "unknown"

        if "one-day delay" in text_lower:
            has_delay = True
            delay_days = 1
            alert_type = "one_day_delay"
        elif "no service" in text_lower:
            has_delay = True
            alert_type = "no_service"
            # Try to extract which days
            # Example: "no service on Monday, Tuesday, Wednesday"
        elif "operating as" in text_lower and "road conditions" in text_lower:
            has_delay = True
            alert_type = "conditional"

        # Extract week information
        week_match = re.search(r"week of (\w+ \d+)", text_lower)
        week_of = week_match.group(1) if week_match else None

        return {
            "text": text,
            "has_delay": has_delay,
            "delay_days": delay_days,
            "alert_type": alert_type,
            "week_of": week_of,
        }
