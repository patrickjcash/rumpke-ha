"""Test script for holiday schedule HTML parsing."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_parse_holiday_schedule():
    """Test parsing holiday schedule from HTML."""
    # TODO: Implement holiday schedule parser test
    print("Testing holiday schedule parser...")
    pass


async def test_get_region_api():
    """Test the get-region API endpoint."""
    import aiohttp

    print("Testing get-region API...")

    # Example zip codes for testing different regions
    test_zips = {
        "45202": "Cincinnati",
        "44102": "Cleveland",
        "45402": "Dayton",
        "40324": "Bluegrass",
    }

    async with aiohttp.ClientSession() as session:
        for zip_code, expected_region in test_zips.items():
            url = f"https://www.rumpke.com/holiday-schedule/get-region?zipCode={zip_code}"
            async with session.get(url) as response:
                data = await response.json()
                print(f"  Zip {zip_code}: {data.get('region')} (expected: {expected_region})")
                assert data.get("region") == expected_region, f"Region mismatch for {zip_code}"

    print("✓ get-region API tests passed")


if __name__ == "__main__":
    asyncio.run(test_get_region_api())
    # asyncio.run(test_parse_holiday_schedule())
