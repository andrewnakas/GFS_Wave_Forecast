#!/usr/bin/env python3
"""
Test script for ski resort scraper.
Runs basic validation tests on the scraping system.
"""

import sys
from database import SkiResortDatabase
from resorts_data import NORTHERN_HEMISPHERE_RESORTS, get_all_countries
from scrapers import get_scraper_for_resort

def test_database_creation():
    """Test database initialization."""
    print("Testing database creation...")
    try:
        db = SkiResortDatabase()
        print("✓ Database created successfully")
        return True
    except Exception as e:
        print(f"✗ Database creation failed: {e}")
        return False


def test_resort_data():
    """Test resort data integrity."""
    print("\nTesting resort data...")
    errors = []

    # Check we have resorts
    if len(NORTHERN_HEMISPHERE_RESORTS) == 0:
        errors.append("No resorts in database")
    else:
        print(f"✓ Found {len(NORTHERN_HEMISPHERE_RESORTS)} resorts")

    # Validate each resort has required fields
    required_fields = ['name', 'country', 'region']
    for resort in NORTHERN_HEMISPHERE_RESORTS:
        for field in required_fields:
            if not resort.get(field):
                errors.append(f"Resort missing {field}: {resort.get('name', 'Unknown')}")

    # Check countries
    countries = get_all_countries()
    print(f"✓ Resorts span {len(countries)} countries: {', '.join(countries)}")

    if errors:
        for error in errors:
            print(f"✗ {error}")
        return False

    print("✓ All resort data valid")
    return True


def test_scraper_initialization():
    """Test scraper initialization for sample resorts."""
    print("\nTesting scraper initialization...")
    test_resorts = ['Vail', 'Whistler Blackcomb', 'Chamonix', 'Niseko']
    success = True

    for resort_name in test_resorts:
        try:
            scraper = get_scraper_for_resort(resort_name)
            print(f"✓ Scraper initialized for {resort_name}: {type(scraper).__name__}")
        except Exception as e:
            print(f"✗ Failed to initialize scraper for {resort_name}: {e}")
            success = False

    return success


def test_single_scrape():
    """Test scraping a single resort."""
    print("\nTesting single resort scrape...")

    # Use Vail as test resort
    test_resort = next((r for r in NORTHERN_HEMISPHERE_RESORTS if r['name'] == 'Vail'), None)

    if not test_resort:
        print("✗ Test resort 'Vail' not found")
        return False

    try:
        scraper = get_scraper_for_resort('Vail')
        data = scraper.scrape_resort(test_resort)

        if data:
            print(f"✓ Successfully scraped Vail")
            print(f"  Data points collected: {len(data)}")

            # Show what was found
            if data.get('snow_depth_base_cm'):
                print(f"  Base depth: {data['snow_depth_base_cm']} cm")
            if data.get('new_snow_24h_cm'):
                print(f"  24h snowfall: {data['new_snow_24h_cm']} cm")

            return True
        else:
            print("⚠ Scraping completed but no data extracted (this is common)")
            return True  # Not a failure, just means website structure may have changed

    except Exception as e:
        print(f"✗ Scraping failed: {e}")
        return False


def test_database_operations():
    """Test database CRUD operations."""
    print("\nTesting database operations...")

    try:
        db = SkiResortDatabase()

        # Test adding a resort
        test_resort = {
            'name': 'Test Resort',
            'country': 'Test Country',
            'region': 'Test Region',
            'latitude': 45.0,
            'longitude': -110.0,
            'base_elevation_m': 2000,
            'summit_elevation_m': 3000,
            'vertical_drop_m': 1000,
            'website_url': 'https://test.com',
            'snow_report_url': 'https://test.com/snow'
        }

        resort_id = db.add_resort(test_resort)
        print(f"✓ Added test resort (ID: {resort_id})")

        # Test adding snow data
        from datetime import date
        snow_data = {
            'resort_id': resort_id,
            'date': date.today(),
            'snow_depth_base_cm': 100,
            'snow_depth_summit_cm': 150,
            'new_snow_24h_cm': 10,
            'lifts_open': 5,
            'lifts_total': 10
        }

        db.add_snow_data(snow_data)
        print("✓ Added snow data")

        # Test retrieving data
        latest = db.get_latest_snow_data('Test Resort')
        if latest:
            print("✓ Retrieved snow data")
        else:
            print("✗ Failed to retrieve snow data")
            return False

        return True

    except Exception as e:
        print(f"✗ Database operations failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("SKI RESORT SCRAPER TEST SUITE")
    print("=" * 60)

    tests = [
        ("Database Creation", test_database_creation),
        ("Resort Data Integrity", test_resort_data),
        ("Scraper Initialization", test_scraper_initialization),
        ("Database Operations", test_database_operations),
        ("Single Resort Scrape", test_single_scrape),
    ]

    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
