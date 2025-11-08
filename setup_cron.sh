#!/bin/bash
# Script to set up cron job for daily snow data collection
# Run this script to automatically scrape ski resort data daily

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$(which python3)"

# Cron job time (default: 6:00 AM)
CRON_TIME="${1:-0 6 * * *}"

echo "Setting up daily cron job for ski resort data collection"
echo "Project directory: $PROJECT_DIR"
echo "Python path: $PYTHON_PATH"
echo "Schedule: $CRON_TIME"

# Create the cron job command
CRON_CMD="cd $PROJECT_DIR && $PYTHON_PATH collect_data.py --collect >> $PROJECT_DIR/cron.log 2>&1"

# Add to crontab if not already present
(crontab -l 2>/dev/null | grep -v "collect_data.py"; echo "$CRON_TIME $CRON_CMD") | crontab -

echo "Cron job installed successfully!"
echo ""
echo "The scraper will run daily at the scheduled time."
echo "Logs will be written to: $PROJECT_DIR/cron.log"
echo ""
echo "To view current crontab:"
echo "  crontab -l"
echo ""
echo "To remove the cron job:"
echo "  crontab -e"
echo "  (then delete the line containing 'collect_data.py')"
