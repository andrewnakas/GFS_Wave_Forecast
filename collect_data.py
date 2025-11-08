#!/usr/bin/env python3
"""
Main data collection script.
Scrapes snow data from all configured resorts and stores in database.
"""

import argparse
import logging
from datetime import datetime, date
from typing import List, Dict

from database import SkiResortDatabase
from resorts_data import NORTHERN_HEMISPHERE_RESORTS
from scrapers import scrape_all_resorts, get_scraper_for_resort

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ski_resort_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def initialize_database():
    """Initialize database with resort information."""
    logger.info("Initializing database...")
    db = SkiResortDatabase()

    for resort in NORTHERN_HEMISPHERE_RESORTS:
        try:
            db.add_resort(resort)
            logger.debug(f"Added resort: {resort['name']}")
        except Exception as e:
            logger.error(f"Error adding resort {resort['name']}: {e}")

    logger.info(f"Database initialized with {len(NORTHERN_HEMISPHERE_RESORTS)} resorts")


def collect_snow_data(countries: List[str] = None, resorts: List[str] = None):
    """
    Collect current snow data for specified resorts.

    Args:
        countries: List of country names to filter by (e.g., ['USA', 'Canada'])
        resorts: List of specific resort names to scrape
    """
    db = SkiResortDatabase()

    # Filter resorts based on criteria
    resorts_to_scrape = NORTHERN_HEMISPHERE_RESORTS

    if countries:
        resorts_to_scrape = [r for r in resorts_to_scrape
                           if r['country'] in countries]
        logger.info(f"Filtering to countries: {', '.join(countries)}")

    if resorts:
        resorts_to_scrape = [r for r in resorts_to_scrape
                           if r['name'] in resorts]
        logger.info(f"Filtering to specific resorts: {', '.join(resorts)}")

    logger.info(f"Starting scrape of {len(resorts_to_scrape)} resorts...")
    start_time = datetime.now()

    # Scrape all resorts
    results = scrape_all_resorts(resorts_to_scrape, delay=2.0)

    # Store results in database
    success_count = 0
    fail_count = 0

    for resort_info in resorts_to_scrape:
        resort_name = resort_info['name']
        snow_data = results.get(resort_name, {})

        # Get resort ID
        resort_id = db.get_resort_id(resort_name)

        if not resort_id:
            logger.error(f"Resort ID not found for {resort_name}")
            db.log_scraping_attempt(None, 'FAILED',
                                   f'Resort {resort_name} not in database')
            fail_count += 1
            continue

        # Check if we got any meaningful data
        has_data = any(k in snow_data for k in [
            'snow_depth_base_cm', 'snow_depth_summit_cm',
            'new_snow_24h_cm', 'lifts_open', 'runs_open'
        ])

        if has_data:
            try:
                snow_data['resort_id'] = resort_id
                snow_data['date'] = date.today()
                db.add_snow_data(snow_data)
                db.log_scraping_attempt(resort_id, 'SUCCESS',
                                       data_points=len(snow_data))
                success_count += 1
                logger.info(f"✓ Saved data for {resort_name}")
            except Exception as e:
                logger.error(f"✗ Error saving data for {resort_name}: {e}")
                db.log_scraping_attempt(resort_id, 'FAILED', str(e))
                fail_count += 1
        else:
            logger.warning(f"✗ No data extracted for {resort_name}")
            db.log_scraping_attempt(resort_id, 'NO_DATA',
                                   'No data could be extracted from website')
            fail_count += 1

    # Summary
    duration = (datetime.now() - start_time).total_seconds()
    logger.info("=" * 60)
    logger.info(f"Scraping completed in {duration:.1f} seconds")
    logger.info(f"Success: {success_count}/{len(resorts_to_scrape)}")
    logger.info(f"Failed: {fail_count}/{len(resorts_to_scrape)}")
    logger.info("=" * 60)


def show_latest_data(resort_name: str = None):
    """Display latest snow data from database."""
    db = SkiResortDatabase()
    data = db.get_latest_snow_data(resort_name)

    if not data:
        print("No data found in database.")
        return

    print("\n" + "=" * 80)
    print("LATEST SNOW DATA")
    print("=" * 80)

    for record in data:
        print(f"\n{record['name']} ({record['region']}, {record['country']})")
        print(f"  Date: {record['date']}")

        if record.get('snow_depth_base_cm'):
            print(f"  Base Depth: {record['snow_depth_base_cm']} cm")
        if record.get('snow_depth_summit_cm'):
            print(f"  Summit Depth: {record['snow_depth_summit_cm']} cm")
        if record.get('new_snow_24h_cm'):
            print(f"  24h Snowfall: {record['new_snow_24h_cm']} cm")
        if record.get('new_snow_48h_cm'):
            print(f"  48h Snowfall: {record['new_snow_48h_cm']} cm")
        if record.get('new_snow_7d_cm'):
            print(f"  7-Day Snowfall: {record['new_snow_7d_cm']} cm")

        if record.get('lifts_open') and record.get('lifts_total'):
            print(f"  Lifts: {record['lifts_open']}/{record['lifts_total']} open")
        if record.get('runs_open') and record.get('runs_total'):
            print(f"  Runs: {record['runs_open']}/{record['runs_total']} open")

        if record.get('temperature_base_c'):
            print(f"  Temperature: {record['temperature_base_c']}°C")

        print(f"  Scraped: {record['scraped_at']}")

    print("\n" + "=" * 80)


def main():
    """Main entry point with command-line interface."""
    parser = argparse.ArgumentParser(
        description='Ski Resort Snow Data Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize database with all resorts
  python collect_data.py --init

  # Scrape all resorts
  python collect_data.py --collect

  # Scrape only US resorts
  python collect_data.py --collect --countries USA

  # Scrape specific resorts
  python collect_data.py --collect --resorts "Vail" "Whistler Blackcomb"

  # Show latest data
  python collect_data.py --show

  # Show data for specific resort
  python collect_data.py --show --resort "Vail"
        """
    )

    parser.add_argument('--init', action='store_true',
                       help='Initialize database with resort information')
    parser.add_argument('--collect', action='store_true',
                       help='Collect current snow data from resort websites')
    parser.add_argument('--show', action='store_true',
                       help='Show latest snow data from database')
    parser.add_argument('--countries', nargs='+',
                       help='Filter by countries (e.g., USA Canada)')
    parser.add_argument('--resorts', nargs='+',
                       help='Scrape specific resorts by name')
    parser.add_argument('--resort', type=str,
                       help='Show data for specific resort')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Execute requested action
    if args.init:
        initialize_database()

    if args.collect:
        collect_snow_data(countries=args.countries, resorts=args.resorts)

    if args.show:
        show_latest_data(resort_name=args.resort)

    if not (args.init or args.collect or args.show):
        parser.print_help()


if __name__ == '__main__':
    main()
