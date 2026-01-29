"""Utility functions for Rumpke integration."""
from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)


def get_county_from_zip(zip_code: str) -> tuple[str, str] | None:  # type: ignore[syntax]
    """
    Get county and state from zip code.

    Returns tuple of (county_name, state_abbr) or None if not found.
    """
    try:
        import zipcodes

        results = zipcodes.matching(zip_code)

        if results and len(results) > 0:
            result = results[0]
            # Remove " County" suffix if present
            county = result.get("county", "").replace(" County", "")
            state = result.get("state")

            if county and state:
                _LOGGER.debug("Zip %s -> %s County, %s", zip_code, county, state)
                return (county, state)

        _LOGGER.warning("Zip code %s not found in database", zip_code)
        return None
    except ImportError:
        _LOGGER.error("zipcodes library not installed")
        return None
    except Exception as e:
        _LOGGER.error("Error looking up zip %s: %s", zip_code, e)
        return None


def get_city_from_zip(zip_code: str) -> tuple[str, str] | None:  # type: ignore[syntax]
    """
    Get city and state from zip code.

    Returns tuple of (city_name, state_abbr) or None if not found.
    """
    try:
        import zipcodes

        results = zipcodes.matching(zip_code)

        if results and len(results) > 0:
            result = results[0]
            city = result.get("city")
            state = result.get("state")

            if city and state:
                _LOGGER.debug("Zip %s -> %s, %s", zip_code, city, state)
                return (city, state)

        _LOGGER.warning("Zip code %s not found in database", zip_code)
        return None
    except ImportError:
        _LOGGER.error("zipcodes library not installed")
        return None
    except Exception as e:
        _LOGGER.error("Error looking up zip %s: %s", zip_code, e)
        return None
