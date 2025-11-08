"""
Web scraping module for extracting snow conditions from ski resort websites.
Uses multiple strategies to extract snow data from different site formats.
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, date
from typing import Dict, Optional, List
import time
import logging
import json

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
                         '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })

    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage."""
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
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

    def find_json_data(self, soup: BeautifulSoup) -> Dict:
        """Try to extract data from JSON-LD or embedded JSON."""
        data = {}

        # Look for JSON-LD structured data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                json_data = json.loads(script.string)
                # Extract any useful data from structured data
                logger.debug(f"Found JSON-LD data: {json_data}")
            except:
                pass

        # Look for data attributes
        snow_elements = soup.find_all(attrs={'data-snow': True})
        for elem in snow_elements:
            try:
                snow_val = self.extract_number(elem.get('data-snow', ''))
                if snow_val:
                    data['new_snow_24h_cm'] = snow_val
            except:
                pass

        return data

    def extract_from_meta_tags(self, soup: BeautifulSoup) -> Dict:
        """Extract snow data from meta tags."""
        data = {}

        # Look for Open Graph or Twitter meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            content = meta.get('content', '').lower()
            name = (meta.get('name', '') + meta.get('property', '')).lower()

            if 'snow' in name or 'snow' in content:
                # Try to extract numbers
                numbers = re.findall(r'(\d+)\s*(in|inch|cm|")', content)
                if numbers:
                    value, unit = numbers[0]
                    value = int(value)
                    if 'in' in unit or '"' in unit:
                        value = self.inches_to_cm(value)

                    if 'base' in content:
                        data['snow_depth_base_cm'] = value
                    elif 'new' in content or 'fresh' in content:
                        data['new_snow_24h_cm'] = value

        return data

    def parse_snow_report_generic(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        Enhanced generic parser with multiple extraction strategies.
        """
        data = {
            'scraped_url': url,
            'scrape_date': date.today(),
        }

        # Strategy 1: Look for JSON data
        json_data = self.find_json_data(soup)
        data.update(json_data)

        # Strategy 2: Check meta tags
        meta_data = self.extract_from_meta_tags(soup)
        data.update(meta_data)

        # Strategy 3: Look for common HTML structures
        # Find elements with snow-related classes or IDs
        snow_containers = soup.find_all(['div', 'span', 'p', 'td'],
            class_=re.compile(r'snow|depth|powder|condition', re.I))

        for container in snow_containers:
            text = container.get_text().strip()

            # Try to extract snow depth
            if re.search(r'base|lower|bottom', text, re.I):
                depth_match = re.search(r'(\d+)\s*(?:in|inch|"|cm)', text, re.I)
                if depth_match and not data.get('snow_depth_base_cm'):
                    value = int(depth_match.group(1))
                    unit = depth_match.group(0).lower()
                    if 'in' in unit or '"' in unit:
                        value = self.inches_to_cm(value)
                    data['snow_depth_base_cm'] = value

            if re.search(r'summit|top|upper|peak', text, re.I):
                depth_match = re.search(r'(\d+)\s*(?:in|inch|"|cm)', text, re.I)
                if depth_match and not data.get('snow_depth_summit_cm'):
                    value = int(depth_match.group(1))
                    unit = depth_match.group(0).lower()
                    if 'in' in unit or '"' in unit:
                        value = self.inches_to_cm(value)
                    data['snow_depth_summit_cm'] = value

        # Strategy 4: Full text search with comprehensive patterns
        text_content = soup.get_text()

        # Enhanced patterns with more variations
        patterns = {
            'base_depth': [
                r'base[:\s]+(\d+)\s*(?:in|inch|"|cm)',
                r'(?:lower|bottom)[:\s]+(\d+)\s*(?:in|inch|"|cm)',
                r'(\d+)\s*(?:in|inch|"|cm)[:\s]+base',
                r'base\s+depth[:\s]+(\d+)',
                r'snow\s+depth.*?base.*?(\d+)',
            ],
            'summit_depth': [
                r'summit[:\s]+(\d+)\s*(?:in|inch|"|cm)',
                r'(?:top|upper|peak)[:\s]+(\d+)\s*(?:in|inch|"|cm)',
                r'(\d+)\s*(?:in|inch|"|cm)[:\s]+(?:summit|top)',
                r'summit\s+depth[:\s]+(\d+)',
            ],
            '24h_snow': [
                r'(?:24|twenty.?four)\s*(?:hr|hour|h)[:\s]+(\d+)',
                r'overnight[:\s]+(\d+)',
                r'last\s+24[:\s]+(\d+)',
                r'new\s+snow[:\s]+(\d+)',
                r'(?:24|twenty.?four)\s*(?:hr|hour|h).*?(\d+)\s*(?:in|inch|"|cm)',
                r'(\d+)\s*(?:in|inch|"|cm).*?(?:24|overnight|new)',
            ],
            '48h_snow': [
                r'(?:48|forty.?eight)\s*(?:hr|hour|h)[:\s]+(\d+)',
                r'(?:2|two)\s+day[:\s]+(\d+)',
                r'last\s+48[:\s]+(\d+)',
            ],
            '7d_snow': [
                r'(?:7|seven)\s+day[:\s]+(\d+)',
                r'week[:\s]+(\d+)',
                r'last\s+week[:\s]+(\d+)',
            ],
        }

        # Check if units are inches (common in US resorts)
        is_inches = bool(re.search(r'\d+\s*(?:in|inch|")', text_content[:1000]))

        for key, pattern_list in patterns.items():
            if data.get(key.replace('_', '')):  # Skip if already found
                continue

            for pattern in pattern_list:
                matches = re.finditer(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    try:
                        value = int(match.group(1))

                        # Check if unit is specified in the match
                        full_match = match.group(0).lower()
                        if ('in' in full_match or '"' in full_match) or (is_inches and 'cm' not in full_match):
                            value = self.inches_to_cm(value)

                        # Sanity checks
                        if key in ['base_depth', 'summit_depth'] and (value < 5 or value > 1000):
                            continue
                        if key in ['24h_snow', '48h_snow', '7d_snow'] and value > 300:
                            continue

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

                        logger.debug(f"Found {key}: {value} cm using pattern: {pattern}")
                        break
                    except (ValueError, IndexError):
                        continue

                if data.get(key.replace('_', '')):
                    break

        # Strategy 5: Look for lift and trail status
        lifts_match = re.search(r'(\d+)\s*(?:of|/)\s*(\d+)\s+(?:lift|chair)', text_content, re.IGNORECASE)
        if lifts_match:
            data['lifts_open'] = int(lifts_match.group(1))
            data['lifts_total'] = int(lifts_match.group(2))

        runs_match = re.search(r'(\d+)\s*(?:of|/)\s*(\d+)\s+(?:trail|run|piste)', text_content, re.IGNORECASE)
        if runs_match:
            data['runs_open'] = int(runs_match.group(1))
            data['runs_total'] = int(runs_match.group(2))

        # Strategy 6: Temperature extraction
        temp_patterns = [
            r'(\d+)\s*°?\s*[fF](?:\s|$|\.)',  # Fahrenheit
            r'(-?\d+)\s*°?\s*[cC](?:\s|$|\.)',  # Celsius
            r'temp(?:erature)?[:\s]+(\d+)',
        ]

        for pattern in temp_patterns:
            temp_match = re.search(pattern, text_content)
            if temp_match:
                temp = int(temp_match.group(1))
                # Assume Fahrenheit if > 50 or if F is in the match
                if 'f' in temp_match.group(0).lower() or temp > 50:
                    data['temperature_base_c'] = self.fahrenheit_to_celsius(temp)
                else:
                    data['temperature_base_c'] = float(temp)
                break

        return data

    def scrape_resort(self, resort_data: Dict) -> Dict:
        """
        Main method to scrape snow data for a resort.
        Tries multiple URLs and methods.
        """
        logger.info(f"Scraping {resort_data['name']}...")

        # Try snow report URL first, then website URL
        urls_to_try = []
        if resort_data.get('snow_report_url'):
            urls_to_try.append(resort_data['snow_report_url'])
        if resort_data.get('website_url'):
            urls_to_try.append(resort_data['website_url'])

        for url in urls_to_try:
            soup = self.get_page(url)
            if soup:
                data = self.parse_snow_report_generic(soup, url)

                # Check if we got meaningful data
                meaningful_fields = ['snow_depth_base_cm', 'snow_depth_summit_cm',
                                    'new_snow_24h_cm', 'lifts_open', 'runs_open']
                if data and any(data.get(field) for field in meaningful_fields):
                    logger.info(f"Successfully scraped {resort_data['name']} - found {len([k for k in meaningful_fields if data.get(k)])} data points")
                    return data

                time.sleep(1)  # Be polite to servers

        logger.warning(f"Could not extract meaningful data for {resort_data['name']}")

        # Return empty dict with minimal info to show we tried
        return {
            'scraped_url': resort_data.get('snow_report_url') or resort_data.get('website_url'),
            'scrape_date': date.today(),
        }


class VailResortsScraper(SnowDataScraper):
    """
    Specialized scraper for Vail Resorts properties.
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

        # Vail Resorts specific patterns - they often use consistent class names
        try:
            # Common Vail Resorts selectors (may need updating as sites change)
            depth_selectors = [
                {'class': re.compile(r'snow.*depth', re.I)},
                {'class': re.compile(r'depth.*value', re.I)},
                {'data-snow-depth': True},
            ]

            for selector in depth_selectors:
                elements = soup.find_all(['div', 'span', 'p'], selector)
                for elem in elements:
                    text = elem.get_text().strip()
                    numbers = re.findall(r'(\d+)', text)
                    if numbers:
                        value = int(numbers[0])
                        # Vail typically uses inches
                        value_cm = self.inches_to_cm(value)

                        # Determine if base or summit based on context
                        context = str(elem.parent).lower() if elem.parent else ''
                        if 'base' in context or 'lower' in context:
                            data['snow_depth_base_cm'] = value_cm
                        elif 'summit' in context or 'top' in context or 'upper' in context:
                            data['snow_depth_summit_cm'] = value_cm

        except Exception as e:
            logger.debug(f"Vail-specific parsing failed: {e}")

        # Fall back to generic parser
        if not data.get('snow_depth_base_cm'):
            generic_data = self.parse_snow_report_generic(soup, url)
            data.update({k: v for k, v in generic_data.items() if k not in data or not data[k]})

        return data


def get_scraper_for_resort(resort_name: str) -> SnowDataScraper:
    """
    Return appropriate scraper based on resort name.
    """
    # Vail Resorts properties
    vail_resorts = ['Vail', 'Breckenridge', 'Keystone', 'Park City',
                   'Heavenly', 'Stowe', 'Killington']

    if resort_name in vail_resorts:
        return VailResortsScraper()

    # Default to generic scraper
    return SnowDataScraper()


def scrape_all_resorts(resorts_list: list, delay: float = 2.0) -> Dict[str, Dict]:
    """
    Scrape all resorts in the list with a delay between requests.
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
