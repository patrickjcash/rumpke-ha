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


def _is_pickup_in_alert_week(pickup_date: datetime.date, week_of: str) -> bool:
    """
    Check if a pickup date falls within the service alert week.

    Args:
        pickup_date: The pickup date to check
        week_of: Week string from service alert (e.g., "jan. 26" or "Jan. 26")

    Returns:
        True if pickup is in the alert week, False otherwise
    """
    try:
        # Parse the week_of string (e.g., "jan. 26")
        # Format: "Month Day" where month may have period
        import re
        from datetime import datetime as dt

        # Clean up the string and parse
        week_str = week_of.strip().replace(".", "").title()

        # Try to parse with current year first
        year = pickup_date.year
        try:
            # Try "Jan 26" format
            week_start_date = dt.strptime(f"{week_str} {year}", "%b %d %Y").date()
        except ValueError:
            # Try full month name
            week_start_date = dt.strptime(f"{week_str} {year}", "%B %d %Y").date()

        # If parsed date is way in the past (earlier than 6 months ago), use next year
        today = datetime.now().date()
        if week_start_date < today - timedelta(days=180):
            week_start_date = week_start_date.replace(year=year + 1)

        # Calculate week boundaries (Monday-Sunday)
        # The week_of date might be mid-week, so find the Monday of that week
        days_to_monday = week_start_date.weekday()
        week_start = week_start_date - timedelta(days=days_to_monday)
        week_end = week_start + timedelta(days=6)

        result = week_start <= pickup_date <= week_end
        _LOGGER.debug(
            "Alert week check: pickup=%s, week_of=%s, week=%s to %s, result=%s",
            pickup_date,
            week_of,
            week_start,
            week_end,
            result,
        )
        return result

    except Exception as e:
        _LOGGER.warning("Failed to parse week_of '%s': %s - skipping delay for this pickup", week_of, e)
        # If we can't parse, don't apply the delay (safer to skip than incorrectly delay all weeks)
        return False


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

    # Check if a recent pickup (from this week) was delayed to today or a future date
    days_back = from_date.weekday() - service_weekday
    if days_back > 0:  # Service day was earlier this week
        recent_pickup = from_date - timedelta(days=days_back)

        # Calculate what this recent pickup would be with delays
        delayed_pickup = recent_pickup

        # Apply service alert delays
        if service_alert and service_alert.get("has_delay"):
            week_of = service_alert.get("week_of")
            if week_of:
                if _is_pickup_in_alert_week(recent_pickup, week_of):
                    delay_days = service_alert.get("delay_days", 0)
                    if delay_days > 0:
                        delayed_pickup += timedelta(days=delay_days)
            else:
                delay_days = service_alert.get("delay_days", 0)
                if delay_days > 0:
                    delayed_pickup += timedelta(days=delay_days)

        # Apply holiday delays
        delayed_pickup = apply_holiday_delays(delayed_pickup, holidays)

        # If the delayed pickup is today or in the future, return it
        if delayed_pickup >= from_date:
            _LOGGER.debug(
                "Found recent pickup from %s delayed to %s",
                recent_pickup,
                delayed_pickup,
            )
            return delayed_pickup

    # Find the next occurrence of the service day (including today)
    days_ahead = service_weekday - from_date.weekday()
    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7

    next_pickup = from_date + timedelta(days=days_ahead)

    # Apply service alert delays only if pickup is in the affected week
    if service_alert and service_alert.get("has_delay"):
        week_of = service_alert.get("week_of")
        if week_of:
            # Parse week_of date (e.g., "jan. 26" or "Jan. 26")
            if _is_pickup_in_alert_week(next_pickup, week_of):
                delay_days = service_alert.get("delay_days", 0)
                if delay_days > 0:
                    next_pickup += timedelta(days=delay_days)
                    _LOGGER.debug(
                        "Applied service alert delay of %d day(s) to %s (week of %s)",
                        delay_days,
                        next_pickup,
                        week_of,
                    )
        else:
            # No week specified - apply to all pickups (rare case)
            delay_days = service_alert.get("delay_days", 0)
            if delay_days > 0:
                next_pickup += timedelta(days=delay_days)
                _LOGGER.debug(
                    "Applied service alert delay of %d day(s) to %s (no week specified)",
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
