# Ski Resort Snow Data Scraper

A comprehensive Python-based system for collecting and storing daily snow condition data from major ski resorts across the Northern Hemisphere.

## Features

- **50+ Major Ski Resorts**: Covers popular resorts across North America, Europe, and Asia
- **Comprehensive Snow Data**: Collects base/summit snow depth, 24h/48h/7-day snowfall, lift/run status, and more
- **Automated Daily Updates**: Set up scheduled scraping via cron or built-in scheduler
- **SQLite Database**: Persistent storage with historical data tracking
- **Extensible Architecture**: Easy to add new resorts and custom scrapers
- **Robust Scraping**: Generic parser handles various website formats with specialized scrapers for major resort chains

## Covered Regions

### North America
- **USA**: Colorado (Vail, Aspen, Breckenridge), Utah (Park City, Alta, Snowbird), California (Mammoth, Palisades Tahoe), Wyoming (Jackson Hole), Vermont (Stowe, Killington), and more
- **Canada**: British Columbia (Whistler Blackcomb, Revelstoke), Alberta (Lake Louise, Sunshine Village), Quebec (Tremblant)

### Europe
- **France**: Chamonix, Val d'Isère, Courchevel, Les Trois Vallées
- **Switzerland**: Zermatt, Verbier, St. Moritz
- **Austria**: St. Anton, Ischgl, Kitzbühel
- **Italy**: Cortina d'Ampezzo

### Asia
- **Japan**: Niseko, Hakuba Valley, Rusutsu
- **South Korea**: Yongpyong

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd GFS_Wave_Forecast
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**:
   ```bash
   python collect_data.py --init
   ```

## Usage

### Manual Data Collection

Collect snow data from all resorts:
```bash
python collect_data.py --collect
```

Collect data from specific countries:
```bash
python collect_data.py --collect --countries USA Canada
```

Collect data from specific resorts:
```bash
python collect_data.py --collect --resorts "Vail" "Whistler Blackcomb" "Niseko"
```

### View Latest Data

Show all latest snow reports:
```bash
python collect_data.py --show
```

Show data for a specific resort:
```bash
python collect_data.py --show --resort "Vail"
```

### Automated Daily Updates

#### Option 1: Using Built-in Scheduler

Run the scheduler as a daemon (runs continuously):
```bash
python scheduler.py --init --time 06:00
```

Run collection immediately then start scheduler:
```bash
python scheduler.py --init --run-now --time 06:00
```

#### Option 2: Using Cron (Linux/Mac)

Set up a daily cron job (runs at 6:00 AM by default):
```bash
./setup_cron.sh
```

Custom time (e.g., 8:30 AM):
```bash
./setup_cron.sh "30 8 * * *"
```

View installed cron jobs:
```bash
crontab -l
```

## Database Schema

### Tables

**resorts**
- Resort information (name, location, elevation, website URLs)
- One-time or rarely updated data

**snow_data**
- Daily snow conditions for each resort
- Metrics: snow depth (base/summit), new snowfall (24h/48h/7d), lift/run status, temperature, conditions

**scraping_log**
- Tracks all scraping attempts with success/failure status
- Useful for debugging and monitoring

## Data Collected

For each resort, the scraper attempts to collect:

- **Snow Depth**: Base and summit snow depth (cm)
- **New Snowfall**: 24-hour, 48-hour, and 7-day totals (cm)
- **Resort Status**: Number of open lifts and runs vs. total
- **Weather**: Temperature, conditions, visibility
- **Season Stats**: Total seasonal snowfall, last snowfall date
- **Additional Data**: Terrain park status and other resort-specific information

## Architecture

### Core Components

1. **database.py**: SQLite database management with schema and CRUD operations
2. **resorts_data.py**: Comprehensive list of 50+ Northern Hemisphere ski resorts
3. **scrapers.py**: Web scraping engine with generic and specialized scrapers
4. **collect_data.py**: Main script for data collection and CLI interface
5. **scheduler.py**: Daily automation scheduler

### Scraping Strategy

The system uses a multi-tiered approach:

1. **Specialized Scrapers**: Custom parsers for major resort chains (Vail Resorts, etc.)
2. **Generic Parser**: Fallback parser using pattern matching for common snow report formats
3. **Resilient Extraction**: Multiple URL attempts and regex patterns for robust data extraction

## Adding New Resorts

To add a new resort, edit `resorts_data.py` and add an entry:

```python
{
    "name": "Resort Name",
    "country": "Country",
    "region": "State/Province",
    "latitude": 45.0000,
    "longitude": -110.0000,
    "base_elevation_m": 2000,
    "summit_elevation_m": 3000,
    "vertical_drop_m": 1000,
    "website_url": "https://www.resort.com",
    "snow_report_url": "https://www.resort.com/snow-report"
}
```

Then re-initialize the database:
```bash
python collect_data.py --init
```

## Extending with Custom Scrapers

For resorts with unique website formats, create a custom scraper class in `scrapers.py`:

```python
class CustomResortScraper(SnowDataScraper):
    def scrape_resort(self, resort_data: Dict) -> Dict:
        # Custom scraping logic
        pass
```

Update `get_scraper_for_resort()` to use your custom scraper.

## Export Data

The database can be queried directly using SQLite tools:

```bash
sqlite3 ski_resorts.db "SELECT * FROM snow_data WHERE date = date('now') ORDER BY new_snow_24h_cm DESC LIMIT 10"
```

Or use Python:
```python
from database import SkiResortDatabase

db = SkiResortDatabase()
latest_data = db.get_latest_snow_data()
```

## Logs

- **ski_resort_scraper.log**: Main scraping activity log
- **ski_resort_scheduler.log**: Scheduler activity log
- **cron.log**: Cron job execution log (if using cron)

## Troubleshooting

### No Data Extracted

Some resorts may have:
- Changed their website structure
- Implemented anti-scraping measures
- Different data formats requiring custom scrapers

Check the logs for specific errors and consider adding a custom scraper.

### Rate Limiting

The scraper includes delays between requests (default: 2 seconds) to avoid overwhelming servers. If you experience issues:

1. Increase the delay in `scrapers.py`
2. Scrape smaller subsets of resorts
3. Use the country filter to distribute scraping

### Database Issues

Reset the database:
```bash
rm ski_resorts.db
python collect_data.py --init
```

## Contributing

Contributions are welcome! Areas for improvement:

- Add more ski resorts
- Improve scraping accuracy for specific resorts
- Add data visualization/dashboard
- Create REST API for data access
- Add snow forecast integration
- Implement multi-language support

## Legal & Ethics

**Important**: This tool is for personal/educational use. When scraping:

- Respect robots.txt files
- Don't overload resort websites
- Use reasonable delays between requests
- Consider using official APIs where available
- Comply with terms of service

Many resorts provide official APIs or data feeds - please use those when available.

## License

See LICENSE file for details.

## Support

For issues, questions, or contributions, please open an issue on GitHub.
