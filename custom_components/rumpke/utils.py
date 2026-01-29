"""Utility functions for Rumpke integration."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging

from homeassistant.util import dt as dt_util

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


def apply_holiday_delays(pickup_date: datetime.date, holidays: list) -> datetime.date:
    """Apply holiday delays to a pickup date."""
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


def calculate_next_pickup(
    service_day: str,
    holidays: list,
    service_alert: dict | None = None,
    from_date: datetime.date | None = None,
) -> datetime.date | None:
    """
    Calculate next pickup date from a given date.

    Args:
        service_day: Day of week for service (e.g., "Thursday")
        holidays: List of holiday data dicts from coordinator
        service_alert: Service alert dict from coordinator
        from_date: Calculate from this date (defaults to today)

    Returns:
        Next pickup date or None if error
    """
    if from_date is None:
        now = dt_util.now()
        from_date = now.date()

    service_weekday = DAYS.get(service_day)
    if service_weekday is None:
        _LOGGER.error("Invalid service day: %s", service_day)
        return None

    # Find the next occurrence of the service day (including today)
    days_ahead = service_weekday - from_date.weekday()
    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7

    next_pickup = from_date + timedelta(days=days_ahead)

    # Apply service alert delays first
    if service_alert and service_alert.get("has_delay"):
        delay_days = service_alert.get("delay_days", 0)
        if delay_days > 0:
            next_pickup += timedelta(days=delay_days)
            _LOGGER.debug(
                "Applied service alert delay of %d day(s) to %s",
                delay_days,
                next_pickup,
            )

    # Then apply holiday delays
    next_pickup = apply_holiday_delays(next_pickup, holidays)

    return next_pickup


def generate_pickup_dates(
    service_day: str,
    holidays: list,
    service_alert: dict | None,
    start_date: datetime.date,
    end_date: datetime.date,
) -> list[datetime.date]:
    """
    Generate all pickup dates within a date range.

    Args:
        service_day: Day of week for service
        holidays: List of holiday data dicts
        service_alert: Service alert dict
        start_date: Start of date range
        end_date: End of date range

    Returns:
        List of pickup dates within range
    """
    pickup_dates = []
    current_date = start_date

    # Generate pickups until we exceed the end date
    while current_date <= end_date:
        next_pickup = calculate_next_pickup(
            service_day, holidays, service_alert, current_date
        )

        if next_pickup is None:
            break

        if next_pickup <= end_date:
            pickup_dates.append(next_pickup)

        # Move to the day after this pickup to find the next one
        current_date = next_pickup + timedelta(days=1)

    return pickup_dates
