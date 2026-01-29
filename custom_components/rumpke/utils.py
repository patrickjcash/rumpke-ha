"""Utility functions for Rumpke integration."""
from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)


def get_county_from_zip(zip_code: str) -> tuple[str, str] | None:  # type: ignore[syntax]
    """
    Get county and state from zip code using uszipcode library.

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
        else:
            _LOGGER.warning("Zip code %s not found in database", zip_code)
            return None
    except ImportError:
        _LOGGER.error("uszipcode library not installed")
        return None
    except Exception as e:
        _LOGGER.error("Error looking up zip %s: %s", zip_code, e)
        return None
