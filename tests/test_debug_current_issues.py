"""Debug current issues with the integration."""
import asyncio
import logging
from datetime import datetime, timedelta
import sys
import os

# Add component directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'rumpke'))

from api import RumpkeApiClient
from parser import HolidayScheduleParser
from alerts_parser import ServiceAlertsParser
from utils import get_county_from_zip
import aiohttp

logging.basicConfig(level=logging.DEBUG)
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

async def test_city_lookup():
    """Test uszipcode library for city lookup."""
    print("\n" + "="*60)
    print("TEST 1: City/State Lookup")
    print("="*60)

    zip_code = "43065"

    # Test get_county_from_zip
    county_info = get_county_from_zip(zip_code)
    print(f"get_county_from_zip({zip_code}) = {county_info}")

    if county_info:
        county, state = county_info

        # Test uszipcode library
        try:
            from uszipcode import SearchEngine
            search = SearchEngine()
            result = search.by_zipcode(zip_code)

            print(f"\nuszipcode result for {zip_code}:")
            print(f"  major_city: {result.major_city if result else None}")
            print(f"  post_office_city: {result.post_office_city if result else None}")
            print(f"  common_city_list: {result.common_city_list if result else None}")
            print(f"  county: {result.county if result else None}")
            print(f"  state: {result.state if result else None}")

            if result and result.major_city:
                city = result.major_city
                title = f"Rumpke Waste Collection - {city}, {state} {zip_code}"
            else:
                title = f"Rumpke Waste Collection - {county} County, {state} {zip_code}"

            print(f"\nFinal title: {title}")

        except ImportError as e:
            print(f"ERROR: uszipcode not available: {e}")
        except Exception as e:
            print(f"ERROR: {e}")
    else:
        print(f"Could not find county info for {zip_code}")

async def test_service_alerts():
    """Test service alert parsing for Delaware County."""
    print("\n" + "="*60)
    print("TEST 2: Service Alert Parsing")
    print("="*60)

    zip_code = "43065"
    county_info = get_county_from_zip(zip_code)

    if not county_info:
        print("Could not determine county")
        return

    county, state = county_info
    print(f"Testing for: {county} County, {state}")

    async with aiohttp.ClientSession() as session:
        api = RumpkeApiClient(session)
        alerts_html = await api.get_service_alerts_html()

        if not alerts_html:
            print("Failed to fetch alerts HTML")
            return

        service_alert = ServiceAlertsParser.parse(alerts_html, county, state)

        print(f"\nService alert result:")
        if service_alert:
            print(f"  alert_type: {service_alert.get('alert_type')}")
            print(f"  has_delay: {service_alert.get('has_delay')}")
            print(f"  delay_days: {service_alert.get('delay_days')}")
            print(f"  week_of: {service_alert.get('week_of')}")
            print(f"  text: {service_alert.get('text')}")
        else:
            print("  No service alert found")

async def test_pickup_calculation():
    """Test next pickup calculation."""
    print("\n" + "="*60)
    print("TEST 3: Pickup Date Calculation")
    print("="*60)

    zip_code = "43065"
    service_day = "Thursday"

    county_info = get_county_from_zip(zip_code)
    if not county_info:
        print("Could not determine county")
        return

    county, state = county_info
    print(f"County: {county}, {state}")
    print(f"Service day: {service_day}")

    async with aiohttp.ClientSession() as session:
        api = RumpkeApiClient(session)

        # Get service alert
        alerts_html = await api.get_service_alerts_html()
        service_alert = None
        if alerts_html:
            service_alert = ServiceAlertsParser.parse(alerts_html, county, state)

        # Get holidays
        html = await api.get_holiday_schedule_html(zip_code)
        holidays = HolidayScheduleParser.parse(html) if html else []

        # Calculate next pickup (simulating sensor logic)
        today = datetime.now().date()
        print(f"\nToday: {today} ({today.strftime('%A')})")

        service_weekday = DAYS.get(service_day)
        print(f"Service weekday number: {service_weekday}")
        print(f"Today weekday number: {today.weekday()}")

        # Base calculation
        days_ahead = service_weekday - today.weekday()
        print(f"Days ahead (before adjustment): {days_ahead}")

        if days_ahead < 0:
            days_ahead += 7

        print(f"Days ahead (after adjustment): {days_ahead}")

        next_pickup = today + timedelta(days=days_ahead)
        print(f"Base next pickup: {next_pickup} ({next_pickup.strftime('%A')})")

        # Apply service alert delays
        if service_alert:
            print(f"\nService alert found:")
            print(f"  has_delay: {service_alert.get('has_delay')}")
            print(f"  delay_days: {service_alert.get('delay_days')}")
            print(f"  week_of: {service_alert.get('week_of')}")

            if service_alert.get("has_delay"):
                delay_days = service_alert.get("delay_days", 0)
                if delay_days > 0:
                    next_pickup += timedelta(days=delay_days)
                    print(f"  Applied {delay_days} day delay")
                    print(f"  New pickup date: {next_pickup} ({next_pickup.strftime('%A')})")
        else:
            print("\nNo service alert found")

        # Apply holiday delays
        print(f"\nChecking {len(holidays)} holidays for delays...")
        week_start = next_pickup - timedelta(days=next_pickup.weekday())
        week_end = week_start + timedelta(days=6)
        print(f"Pickup week: {week_start} to {week_end}")

        for holiday in holidays:
            if not holiday.get("has_delay") or not holiday.get("date"):
                continue

            holiday_date = holiday["date"]

            if week_start <= holiday_date <= week_end and holiday_date <= next_pickup:
                next_pickup += timedelta(days=1)
                print(f"  Delayed by {holiday['name']} on {holiday_date}")

        print(f"\n=== FINAL RESULT ===")
        print(f"Next pickup: {next_pickup} ({next_pickup.strftime('%A, %B %d, %Y')})")
        print(f"Days until pickup: {(next_pickup - today).days}")

async def main():
    """Run all tests."""
    await test_city_lookup()
    await test_service_alerts()
    await test_pickup_calculation()

if __name__ == "__main__":
    asyncio.run(main())
