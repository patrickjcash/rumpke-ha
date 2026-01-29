"""HTML parser for Rumpke schedules."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)


class HolidayScheduleParser:
    """Parser for Rumpke holiday schedule HTML."""

    @staticmethod
    def parse(html: str) -> list[dict[str, Any]]:
        """Parse holiday schedule HTML and return structured data."""
        soup = BeautifulSoup(html, "html.parser")
        holidays = []

        # Find all holiday accordion sections
        accordion_sections = soup.find_all("div", class_="repeatable-content")

        for section in accordion_sections:
            try:
                # Get the holiday name from the previous H3 tag
                h3 = section.find_previous("h3", class_="tab")
                if not h3:
                    continue

                holiday_name = h3.get_text(strip=True)

                # Get the content div
                content_div = section.find("div", class_="text")
                if not content_div:
                    continue

                # Extract date from h3 inside content
                date_h3 = content_div.find("h3")
                date_str = date_h3.get_text(strip=True) if date_h3 else None

                # Parse the date
                holiday_date = None
                if date_str:
                    # Try multiple date formats
                    formats = [
                        "%A, %B %d, %Y",      # Monday, May 25, 2026
                        "%A, %b. %d, %Y",     # Monday, Jan. 19, 2026
                        "%A, %b %d, %Y",      # Monday, Jan 19, 2026
                    ]
                    # Handle "Sept." abbreviation (strptime doesn't recognize it)
                    date_str_normalized = date_str.replace("Sept.", "Sep.")
                    for fmt in formats:
                        try:
                            holiday_date = datetime.strptime(date_str_normalized, fmt).date()
                            break
                        except ValueError:
                            continue

                    if not holiday_date:
                        _LOGGER.warning("Could not parse date: %s", date_str)

                # Extract all paragraphs
                paragraphs = content_div.find_all("p")
                details = [p.get_text(strip=True) for p in paragraphs]

                # Determine if there's a service delay
                has_delay = HolidayScheduleParser._check_for_delay(details)
                exceptions = HolidayScheduleParser._extract_exceptions(details)

                holiday_data = {
                    "name": holiday_name,
                    "date": holiday_date,
                    "date_str": date_str,
                    "has_delay": has_delay,
                    "details": details,
                    "exceptions": exceptions,
                }

                holidays.append(holiday_data)
                _LOGGER.debug("Parsed holiday: %s on %s (delay: %s)", holiday_name, holiday_date, has_delay)

            except Exception as e:
                _LOGGER.error("Error parsing holiday section: %s", e)
                continue

        return holidays

    @staticmethod
    def _check_for_delay(details: list[str]) -> bool:
        """Check if the holiday causes service delays."""
        delay_keywords = [
            "service will not occur",
            "no service",
            "delayed one day",
            "will move to",
            "move to saturday",
        ]

        details_text = " ".join(details).lower()

        # Check for explicit "no delays" message
        if "no service delays" in details_text:
            return False

        # Check for delay keywords
        return any(keyword in details_text for keyword in delay_keywords)

    @staticmethod
    def _extract_exceptions(details: list[str]) -> list[str]:
        """Extract exception notes from holiday details."""
        exceptions = []
        for detail in details:
            if "exception" in detail.lower() or "note:" in detail.lower():
                exceptions.append(detail)
        return exceptions
