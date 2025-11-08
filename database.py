"""
Database module for ski resort snow data.
Handles schema creation and data persistence.
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json


class SkiResortDatabase:
    """Manages the ski resort snow data database."""

    def __init__(self, db_path: str = "ski_resorts.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.create_tables()

    def get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)

    def create_tables(self):
        """Create database tables if they don't exist."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Resorts table - stores static/semi-static resort information
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resorts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                country TEXT NOT NULL,
                region TEXT,
                latitude REAL,
                longitude REAL,
                base_elevation_m INTEGER,
                summit_elevation_m INTEGER,
                vertical_drop_m INTEGER,
                website_url TEXT,
                snow_report_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Snow data table - stores daily snow conditions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snow_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resort_id INTEGER NOT NULL,
                date DATE NOT NULL,
                snow_depth_base_cm INTEGER,
                snow_depth_summit_cm INTEGER,
                new_snow_24h_cm INTEGER,
                new_snow_48h_cm INTEGER,
                new_snow_7d_cm INTEGER,
                snow_condition TEXT,
                last_snowfall_date DATE,
                season_total_cm INTEGER,
                lifts_open INTEGER,
                lifts_total INTEGER,
                runs_open INTEGER,
                runs_total INTEGER,
                temperature_base_c REAL,
                temperature_summit_c REAL,
                weather_condition TEXT,
                wind_speed_kmh REAL,
                visibility TEXT,
                terrain_park_status TEXT,
                additional_data TEXT,  -- JSON field for extra data
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resort_id) REFERENCES resorts (id),
                UNIQUE(resort_id, date)
            )
        """)

        # Forecast data table - stores snow forecasts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snow_forecast (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resort_id INTEGER NOT NULL,
                forecast_date DATE NOT NULL,
                predicted_snowfall_cm INTEGER,
                temperature_high_c REAL,
                temperature_low_c REAL,
                weather_condition TEXT,
                wind_speed_kmh REAL,
                forecast_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resort_id) REFERENCES resorts (id)
            )
        """)

        # Scraping log table - tracks scraping attempts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraping_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resort_id INTEGER,
                scrape_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                error_message TEXT,
                data_points_collected INTEGER,
                FOREIGN KEY (resort_id) REFERENCES resorts (id)
            )
        """)

        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_snow_data_date
            ON snow_data(date DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_snow_data_resort_date
            ON snow_data(resort_id, date DESC)
        """)

        conn.commit()
        conn.close()

    def add_resort(self, resort_data: Dict) -> int:
        """Add a new resort to the database."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO resorts
            (name, country, region, latitude, longitude, base_elevation_m,
             summit_elevation_m, vertical_drop_m, website_url, snow_report_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            resort_data.get('name'),
            resort_data.get('country'),
            resort_data.get('region'),
            resort_data.get('latitude'),
            resort_data.get('longitude'),
            resort_data.get('base_elevation_m'),
            resort_data.get('summit_elevation_m'),
            resort_data.get('vertical_drop_m'),
            resort_data.get('website_url'),
            resort_data.get('snow_report_url')
        ))

        resort_id = cursor.lastrowid
        if resort_id == 0:
            # Resort already exists, get its ID
            cursor.execute("SELECT id FROM resorts WHERE name = ?",
                         (resort_data.get('name'),))
            resort_id = cursor.fetchone()[0]

        conn.commit()
        conn.close()
        return resort_id

    def add_snow_data(self, snow_data: Dict) -> bool:
        """Add daily snow data for a resort."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Prepare additional data as JSON if present
            additional_data = snow_data.get('additional_data')
            if additional_data and not isinstance(additional_data, str):
                additional_data = json.dumps(additional_data)

            cursor.execute("""
                INSERT OR REPLACE INTO snow_data
                (resort_id, date, snow_depth_base_cm, snow_depth_summit_cm,
                 new_snow_24h_cm, new_snow_48h_cm, new_snow_7d_cm,
                 snow_condition, last_snowfall_date, season_total_cm,
                 lifts_open, lifts_total, runs_open, runs_total,
                 temperature_base_c, temperature_summit_c, weather_condition,
                 wind_speed_kmh, visibility, terrain_park_status, additional_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snow_data.get('resort_id'),
                snow_data.get('date', datetime.now().date()),
                snow_data.get('snow_depth_base_cm'),
                snow_data.get('snow_depth_summit_cm'),
                snow_data.get('new_snow_24h_cm'),
                snow_data.get('new_snow_48h_cm'),
                snow_data.get('new_snow_7d_cm'),
                snow_data.get('snow_condition'),
                snow_data.get('last_snowfall_date'),
                snow_data.get('season_total_cm'),
                snow_data.get('lifts_open'),
                snow_data.get('lifts_total'),
                snow_data.get('runs_open'),
                snow_data.get('runs_total'),
                snow_data.get('temperature_base_c'),
                snow_data.get('temperature_summit_c'),
                snow_data.get('weather_condition'),
                snow_data.get('wind_speed_kmh'),
                snow_data.get('visibility'),
                snow_data.get('terrain_park_status'),
                additional_data
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            conn.close()
            raise e

    def log_scraping_attempt(self, resort_id: Optional[int], status: str,
                            error_message: Optional[str] = None,
                            data_points: int = 0):
        """Log a scraping attempt."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO scraping_log
            (resort_id, status, error_message, data_points_collected)
            VALUES (?, ?, ?, ?)
        """, (resort_id, status, error_message, data_points))

        conn.commit()
        conn.close()

    def get_latest_snow_data(self, resort_name: Optional[str] = None) -> List[Dict]:
        """Get the latest snow data for all resorts or a specific resort."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if resort_name:
            cursor.execute("""
                SELECT r.name, r.country, r.region, s.*
                FROM snow_data s
                JOIN resorts r ON s.resort_id = r.id
                WHERE r.name = ?
                ORDER BY s.date DESC
                LIMIT 1
            """, (resort_name,))
        else:
            cursor.execute("""
                SELECT r.name, r.country, r.region, s.*
                FROM snow_data s
                JOIN resorts r ON s.resort_id = r.id
                WHERE s.date = (
                    SELECT MAX(date) FROM snow_data WHERE resort_id = s.resort_id
                )
                ORDER BY r.name
            """)

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_resort_id(self, name: str) -> Optional[int]:
        """Get resort ID by name."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM resorts WHERE name = ?", (name,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_all_resorts(self) -> List[Dict]:
        """Get all resorts from the database."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resorts ORDER BY name")
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
