"""Full integration test with service alerts."""
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
from alerts_parser import ServiceAlertsParser
from zipcode_lookup import get_county_from_zip

# Test configuration - EXAMPLE DATA
# Replace with your own zip code and service day for testing
TEST_ZIP = "45202"  # Example: Cincinnati, OH
TEST_SERVICE_DAY = "Monday"  # Example service day


def calculate_next_pickup(
    service_day: str, holidays: list, service_alert: dict | None
) -> Optional[datetime.date]:
    """Calculate next pickup date considering holidays AND service alerts."""
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
    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7

    next_pickup = today + timedelta(days=days_ahead)
    print(f"Next {service_day}: {next_pickup.strftime('%A, %B %d, %Y')}")

    # Apply service alert delays first
    if service_alert and service_alert.get("has_delay"):
        print(f"  ⚠️  SERVICE ALERT: {service_alert.get('alert_type')}")
        print(f"     {service_alert.get('text', '')[:100]}...")

        if service_alert.get("delay_days"):
            delay = service_alert["delay_days"]
            next_pickup += timedelta(days=delay)
            print(f"  → Delayed {delay} day(s) due to alert: {next_pickup}")

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
            print(f"  → Delayed by {holiday['name']} on {holiday_date}: {next_pickup}")

    if not affected_holidays and not (service_alert and service_alert.get("has_delay")):
        print("  ✓ No holidays or alerts affecting this pickup")

    return next_pickup


async def main():
    """Main test function."""
    print(f"Testing FULL Rumpke integration with:")
    print(f"  Zip Code: {TEST_ZIP}")
    print(f"  Service Day: {TEST_SERVICE_DAY}")
    print(f"  Today: {datetime.now().strftime('%A, %B %d, %Y')}")
    print()

    # Lookup county from zip
    print("=" * 60)
    print("STEP 1: Zip to County Lookup")
    print("=" * 60)
    county_info = get_county_from_zip(TEST_ZIP)
    if county_info:
        county, state = county_info
        print(f"✓ {TEST_ZIP} → {county} County, {state}")
    else:
        print(f"✗ Could not determine county for zip {TEST_ZIP}")
        return
    print()

    async with aiohttp.ClientSession() as session:
        api = RumpkeApiClient(session)

        # Get region
        print("=" * 60)
        print("STEP 2: Get Region")
        print("=" * 60)
        region_data = await api.get_region(TEST_ZIP)
        if region_data:
            print(f"✓ Region: {region_data.get('region')}, Area: {region_data.get('area')}")
        else:
            print("✗ Failed to get region")
            return
        print()

        # Get holiday schedule
        print("=" * 60)
        print("STEP 3: Get Holiday Schedule")
        print("=" * 60)
        html = await api.get_holiday_schedule_html(TEST_ZIP)
        if html:
            print(f"✓ Retrieved HTML ({len(html)} bytes)")
            holidays = HolidayScheduleParser.parse(html)
            print(f"✓ Parsed {len(holidays)} holidays")
        else:
            print("✗ Failed to get holiday schedule")
            return
        print()

        # Get service alerts
        print("=" * 60)
        print("STEP 4: Get Service Alerts")
        print("=" * 60)
        alerts_html = await api.get_service_alerts_html()
        service_alert = None
        if alerts_html:
            print(f"✓ Retrieved alerts HTML ({len(alerts_html)} bytes)")
            service_alert = ServiceAlertsParser.parse(alerts_html, county, state)
            if service_alert:
                print(f"⚠️  ALERT FOUND for {county} County, {state}:")
                print(f"   Type: {service_alert.get('alert_type')}")
                print(f"   Text: {service_alert.get('text')}")
            else:
                print(f"✓ No active alerts for {county} County, {state}")
        else:
            print("✗ Failed to get service alerts")
        print()

        # Calculate next pickup
        print("=" * 60)
        print("STEP 5: Calculate Next Pickup Date")
        print("=" * 60)
        next_pickup = calculate_next_pickup(TEST_SERVICE_DAY, holidays, service_alert)
        if next_pickup:
            days_until = (next_pickup - datetime.now().date()).days
            print()
            print(f"📅 NEXT PICKUP: {next_pickup.strftime('%A, %B %d, %Y')}")
            print(f"   Days until pickup: {days_until}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
