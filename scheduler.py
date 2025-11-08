#!/usr/bin/env python3
"""
Scheduler for daily automated snow data collection.
Can be run as a daemon or via cron job.
"""

import schedule
import time
import logging
from datetime import datetime
from collect_data import collect_snow_data, initialize_database
from database import SkiResortDatabase

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ski_resort_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def daily_update_job():
    """Job to run daily snow data collection."""
    logger.info("=" * 60)
    logger.info(f"Starting daily snow data collection at {datetime.now()}")
    logger.info("=" * 60)

    try:
        # Collect data from all resorts
        collect_snow_data()
        logger.info("Daily update completed successfully")
    except Exception as e:
        logger.error(f"Error during daily update: {e}", exc_info=True)


def run_scheduler(run_time: str = "06:00"):
    """
    Run the scheduler continuously.

    Args:
        run_time: Time to run daily update in 24-hour format (e.g., "06:00")
    """
    logger.info(f"Starting scheduler - will run daily at {run_time}")

    # Schedule daily job
    schedule.every().day.at(run_time).do(daily_update_job)

    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Daily scheduler for ski resort snow data collection'
    )
    parser.add_argument('--time', type=str, default='06:00',
                       help='Time to run daily update (24-hour format, e.g., 06:00)')
    parser.add_argument('--run-now', action='store_true',
                       help='Run collection immediately instead of waiting for scheduled time')
    parser.add_argument('--init', action='store_true',
                       help='Initialize database before starting scheduler')

    args = parser.parse_args()

    if args.init:
        logger.info("Initializing database...")
        initialize_database()

    if args.run_now:
        logger.info("Running collection immediately...")
        daily_update_job()

    # Start scheduler
    run_scheduler(run_time=args.time)
