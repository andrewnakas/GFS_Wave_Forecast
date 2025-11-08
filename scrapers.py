"""
Web scraping module for extracting snow conditions from ski resort websites.
Uses multiple strategies to extract snow data from different site formats.
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, date
from typing import Dict, Optional
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SnowDataScraper:
    """Base scraper class for extracting snow data from resort websites."""

    def __init__(self, timeout: int = 10):
        """Initialize scraper with custom timeout."""
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def extract_number(self, text: str) -> Optional[int]:
        """Extract first number from text string."""
        if not text:
            return None
        # Remove commas and extract digits
        match = re.search(r'(\d+)', text.replace(',', ''))
        return int(match.group(1)) if match else None

    def extract_decimal(self, text: str) -> Optional[float]:
        """Extract decimal number from text string."""
        if not text:
            return None
        match = re.search(r'(\d+\.?\d*)', text.replace(',', ''))
        return float(match.group(1)) if match else None

    def inches_to_cm(self, inches: float) -> int:
        """Convert inches to centimeters."""
        return int(inches * 2.54)

    def fahrenheit_to_celsius(self, fahrenheit: float) -> float:
        """Convert Fahrenheit to Celsius."""
        return round((fahrenheit - 32) * 5/9, 1)

    def parse_snow_report_generic(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        Generic parser that looks for common patterns across resort websites.
        This tries to extract data even from unseen formats.
        """
        data = {
            'scraped_url': url,
            'scrape_date': date.today(),
        }

        # Common keywords to search for
        text_content = soup.get_text().lower()

        # Try to find snow depth information
        patterns = {
            'base_depth': [
                r'base.*?(\d+)[\s"]*(in|inch|cm)',
                r'(\d+)[\s"]*(in|inch|cm).*?base',
                r'lower.*?(\d+)[\s"]*(in|inch|cm)',
            ],
            'summit_depth': [
                r'summit.*?(\d+)[\s"]*(in|inch|cm)',
                r'(\d+)[\s"]*(in|inch|cm).*?summit',
                r'upper.*?(\d+)[\s"]*(in|inch|cm)',
                r'top.*?(\d+)[\s"]*(in|inch|cm)',
            ],
            '24h_snow': [
                r'24.*?hour.*?(\d+)[\s"]*(in|inch|cm)',
                r'overnight.*?(\d+)[\s"]*(in|inch|cm)',
                r'last.*?24.*?(\d+)[\s"]*(in|inch|cm)',
            ],
            '48h_snow': [
                r'48.*?hour.*?(\d+)[\s"]*(in|inch|cm)',
                r'two.*?day.*?(\d+)[\s"]*(in|inch|cm)',
            ],
            '7d_snow': [
                r'7.*?day.*?(\d+)[\s"]*(in|inch|cm)',
                r'week.*?(\d+)[\s"]*(in|inch|cm)',
            ],
        }

        # Search for patterns
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    value = int(match.group(1))
                    unit = match.group(2).lower()
                    # Convert to cm if in inches
                    if 'in' in unit:
                        value = self.inches_to_cm(value)

                    # Map to database fields
                    if key == 'base_depth':
                        data['snow_depth_base_cm'] = value
                    elif key == 'summit_depth':
                        data['snow_depth_summit_cm'] = value
                    elif key == '24h_snow':
                        data['new_snow_24h_cm'] = value
                    elif key == '48h_snow':
                        data['new_snow_48h_cm'] = value
                    elif key == '7d_snow':
                        data['new_snow_7d_cm'] = value
                    break

        # Try to find lift status
        lifts_match = re.search(r'(\d+)[\s/]*of[\s/]*(\d+).*?lift', text_content, re.IGNORECASE)
        if lifts_match:
            data['lifts_open'] = int(lifts_match.group(1))
            data['lifts_total'] = int(lifts_match.group(2))

        # Try to find run/trail status
        runs_match = re.search(r'(\d+)[\s/]*of[\s/]*(\d+).*?(trail|run)', text_content, re.IGNORECASE)
        if runs_match:
            data['runs_open'] = int(runs_match.group(1))
            data['runs_total'] = int(runs_match.group(2))

        # Try to find temperature
        temp_match = re.search(r'(\d+)[\s]*°?[fFcC]', text_content)
        if temp_match:
            temp = int(temp_match.group(1))
            # Assume Fahrenheit if > 50, else Celsius
            if temp > 50:
                data['temperature_base_c'] = self.fahrenheit_to_celsius(temp)
            else:
                data['temperature_base_c'] = float(temp)

        return data

    def scrape_resort(self, resort_data: Dict) -> Dict:
        """
        Main method to scrape snow data for a resort.
        Tries multiple URLs and methods.
        """
        logger.info(f"Scraping {resort_data['name']}...")

        # Try snow report URL first
        urls_to_try = []
        if resort_data.get('snow_report_url'):
            urls_to_try.append(resort_data['snow_report_url'])
        if resort_data.get('website_url'):
            urls_to_try.append(resort_data['website_url'])

        for url in urls_to_try:
            soup = self.get_page(url)
            if soup:
                data = self.parse_snow_report_generic(soup, url)
                if data and any(k in data for k in ['snow_depth_base_cm', 'new_snow_24h_cm']):
                    logger.info(f"Successfully scraped {resort_data['name']}")
                    return data
                time.sleep(1)  # Be polite to servers

        logger.warning(f"Could not extract data for {resort_data['name']}")
        return {}


class VailResortsScraper(SnowDataScraper):
    """
    Specialized scraper for Vail Resorts properties.
    Handles Vail, Breckenridge, Keystone, Park City, Heavenly, etc.
    """

    def scrape_resort(self, resort_data: Dict) -> Dict:
        """Scrape Vail Resorts snow report format."""
        url = resort_data.get('snow_report_url') or resort_data.get('website_url')
        if not url:
            return {}

        soup = self.get_page(url)
        if not soup:
            return {}

        data = {'scraped_url': url, 'scrape_date': date.today()}

        try:
            # Vail Resorts typically use specific classes/IDs for snow data
            # This is a template - actual class names may vary

            # Look for snow depth containers
            snow_depth_elements = soup.find_all(['div', 'span'],
                                                class_=re.compile(r'snow.*depth|depth.*snow', re.I))

            for elem in snow_depth_elements:
                text = elem.get_text()
                if 'base' in text.lower():
                    depth = self.extract_number(text)
                    if depth:
                        data['snow_depth_base_cm'] = self.inches_to_cm(depth)
                elif 'summit' in text.lower() or 'top' in text.lower():
                    depth = self.extract_number(text)
                    if depth:
                        data['snow_depth_summit_cm'] = self.inches_to_cm(depth)

            # Look for new snowfall
            new_snow = soup.find_all(['div', 'span'],
                                    class_=re.compile(r'new.*snow|snowfall', re.I))
            for elem in new_snow:
                text = elem.get_text()
                if '24' in text or 'overnight' in text.lower():
                    snow = self.extract_number(text)
                    if snow:
                        data['new_snow_24h_cm'] = self.inches_to_cm(snow)

            # Generic fallback
            if not data.get('snow_depth_base_cm'):
                generic_data = self.parse_snow_report_generic(soup, url)
                data.update(generic_data)

        except Exception as e:
            logger.error(f"Error parsing Vail resort {resort_data['name']}: {e}")

        return data


class AltibirdScraper(SnowDataScraper):
    """
    Scraper for Alta and Snowbird (Utah resorts).
    These often have custom formats.
    """

    def scrape_resort(self, resort_data: Dict) -> Dict:
        """Scrape Alta/Snowbird format."""
        url = resort_data.get('snow_report_url') or resort_data.get('website_url')
        if not url:
            return {}

        soup = self.get_page(url)
        if not soup:
            return {}

        data = {'scraped_url': url, 'scrape_date': date.today()}

        # These resorts typically have very clean, text-based snow reports
        data = self.parse_snow_report_generic(soup, url)

        return data


def get_scraper_for_resort(resort_name: str) -> SnowDataScraper:
    """
    Return appropriate scraper based on resort name.
    Falls back to generic scraper if no specialized one exists.
    """
    # Vail Resorts properties
    vail_resorts = ['Vail', 'Breckenridge', 'Keystone', 'Park City',
                   'Heavenly', 'Stowe', 'Killington']

    if resort_name in vail_resorts:
        return VailResortsScraper()

    if resort_name in ['Alta', 'Snowbird']:
        return AltibirdScraper()

    # Default to generic scraper
    return SnowDataScraper()


def scrape_all_resorts(resorts_list: list, delay: float = 2.0) -> Dict[str, Dict]:
    """
    Scrape all resorts in the list with a delay between requests.

    Args:
        resorts_list: List of resort dictionaries
        delay: Seconds to wait between requests (be nice to servers!)

    Returns:
        Dictionary mapping resort names to scraped data
    """
    results = {}

    for i, resort in enumerate(resorts_list):
        logger.info(f"Processing resort {i+1}/{len(resorts_list)}: {resort['name']}")

        scraper = get_scraper_for_resort(resort['name'])
        data = scraper.scrape_resort(resort)

        results[resort['name']] = data

        # Be polite - don't hammer servers
        if i < len(resorts_list) - 1:
            time.sleep(delay)

    return results
