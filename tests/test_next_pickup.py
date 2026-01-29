"""Test script for calculating next pickup date."""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import aiohttp

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "rumpke"))

from api import RumpkeApiClient
from parser import HolidayScheduleParser

# Test configuration - EXAMPLE DATA
# Replace with your own zip code and service day for testing
TEST_ZIP = "45202"  # Example: Cincinnati, OH
TEST_SERVICE_DAY = "Monday"  # Example service day


def calculate_next_pickup(service_day: str, holidays: list) -> Optional[datetime.date]:
    """Calculate next pickup date considering holidays."""
    DAYS = {
        "Monday": 0,
        "Tuesday": 1,
        "Wednesday": 2,
        "Thursday": 3,
        "Friday": 4,
        "Saturday": 5,
        "Sunday": 6,
    }

    today = datetime.now().date()
    service_weekday = DAYS.get(service_day)

    if service_weekday is None:
        print(f"ERROR: Invalid service day: {service_day}")
        return None

    # Find the next occurrence of the service day (including today)
    days_ahead = service_weekday - today.weekday()
    if days_ahead < 0:  # Target day already happened this week (but not today)
        days_ahead += 7

    next_pickup = today + timedelta(days=days_ahead)
    print(f"Next {service_day}: {next_pickup.strftime('%A, %B %d, %Y')}")

    # Check for holidays affecting this pickup
    week_start = next_pickup - timedelta(days=next_pickup.weekday())
    week_end = week_start + timedelta(days=6)

    print(f"Week range: {week_start} to {week_end}")

    affected_holidays = []
    for holiday in holidays:
        if not holiday.get("has_delay") or not holiday.get("date"):
            continue

        holiday_date = holiday["date"]
        if week_start <= holiday_date <= week_end and holiday_date <= next_pickup:
            affected_holidays.append(holiday)
            next_pickup += timedelta(days=1)
            print(f"  Delayed by {holiday['name']} on {holiday_date} -> new date: {next_pickup}")

    if not affected_holidays:
        print("  No holidays affecting this pickup")

    return next_pickup


async def main():
    """Main test function."""
    print(f"Testing Rumpke integration with:")
    print(f"  Zip Code: {TEST_ZIP}")
    print(f"  Service Day: {TEST_SERVICE_DAY}")
    print(f"  Today: {datetime.now().strftime('%A, %B %d, %Y')}")
    print()

    async with aiohttp.ClientSession() as session:
        api = RumpkeApiClient(session)

        # Test 1: Get region
        print("=" * 60)
        print("TEST 1: Get Region")
        print("=" * 60)
        region_data = await api.get_region(TEST_ZIP)
        if region_data:
            print(f"✓ Region: {region_data.get('region')}")
            print(f"  Area: {region_data.get('area')}")
            print(f"  Page Slug: {region_data.get('pageSlug')}")
        else:
            print("✗ Failed to get region")
            return
        print()

        # Test 2: Get holiday schedule HTML
        print("=" * 60)
        print("TEST 2: Get Holiday Schedule")
        print("=" * 60)
        html = await api.get_holiday_schedule_html(TEST_ZIP)
        if html:
            print(f"✓ Retrieved HTML ({len(html)} bytes)")
        else:
            print("✗ Failed to get holiday schedule")
            return
        print()

        # Test 3: Parse holidays
        print("=" * 60)
        print("TEST 3: Parse Holiday Schedule")
        print("=" * 60)
        holidays = HolidayScheduleParser.parse(html)
        print(f"✓ Parsed {len(holidays)} holidays")
        print()

        # Show upcoming holidays with delays
        print("Upcoming holidays with service delays:")
        today = datetime.now().date()
        for holiday in holidays:
            if holiday.get("date") and holiday.get("date") >= today and holiday.get("has_delay"):
                print(f"  • {holiday['name']}: {holiday['date'].strftime('%A, %B %d, %Y')}")
                for detail in holiday['details'][:2]:  # Show first 2 detail lines
                    print(f"    {detail}")
        print()

        # Test 4: Calculate next pickup
        print("=" * 60)
        print("TEST 4: Calculate Next Pickup Date")
        print("=" * 60)
        next_pickup = calculate_next_pickup(TEST_SERVICE_DAY, holidays)
        if next_pickup:
            days_until = (next_pickup - datetime.now().date()).days
            print()
            print(f"📅 NEXT PICKUP: {next_pickup.strftime('%A, %B %d, %Y')}")
            print(f"   Days until pickup: {days_until}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
