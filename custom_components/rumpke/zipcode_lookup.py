"""Zip code to county/state lookup."""
from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

# Fallback mapping for example Rumpke service area zip codes
# This is used when uszipcode library is not available or fails
# Format: zip -> (county, state_abbr)
# These are EXAMPLE zip codes for common service areas
FALLBACK_ZIP_MAP = {
    "45202": ("Hamilton", "OH"),  # Example: Cincinnati, OH
    "44102": ("Cuyahoga", "OH"),  # Example: Cleveland, OH
    "45402": ("Montgomery", "OH"),  # Example: Dayton, OH
    "47201": ("Clark", "IN"),     # Example: Louisville area, IN
}


def get_county_from_zip(zip_code: str) -> tuple[str, str] | None:  # type: ignore[syntax]
    """
    Get county and state from zip code.

    Returns tuple of (county_name, state_abbr) or None if not found.
    """
    try:
        from uszipcode import SearchEngine

        search = SearchEngine()
        result = search.by_zipcode(zip_code)

        if result and result.county:
            # Remove " County" suffix if present
            county = result.county.replace(" County", "")
            state = result.state
            _LOGGER.debug("Zip %s -> %s County, %s", zip_code, county, state)
            return (county, state)
    except ImportError:
        _LOGGER.warning("uszipcode not installed, using fallback")
    except Exception as e:
        _LOGGER.error("Error looking up zip %s: %s", zip_code, e)

    # Fallback to hardcoded map
    if zip_code in FALLBACK_ZIP_MAP:
        _LOGGER.debug("Using fallback for zip %s", zip_code)
        return FALLBACK_ZIP_MAP[zip_code]

    return None
