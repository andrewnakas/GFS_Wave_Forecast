#!/usr/bin/env python3
"""
Data export utility for ski resort snow data.
Export database contents to CSV, JSON, or generate reports.
"""

import csv
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
import argparse


class DataExporter:
    """Export ski resort data in various formats."""

    def __init__(self, db_path: str = "ski_resorts.db"):
        self.db_path = db_path

    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def export_latest_to_csv(self, output_file: str = "latest_snow_data.csv"):
        """Export latest snow data for all resorts to CSV."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                r.name,
                r.country,
                r.region,
                r.base_elevation_m,
                r.summit_elevation_m,
                s.date,
                s.snow_depth_base_cm,
                s.snow_depth_summit_cm,
                s.new_snow_24h_cm,
                s.new_snow_48h_cm,
                s.new_snow_7d_cm,
                s.season_total_cm,
                s.lifts_open,
                s.lifts_total,
                s.runs_open,
                s.runs_total,
                s.temperature_base_c,
                s.weather_condition,
                s.scraped_at
            FROM snow_data s
            JOIN resorts r ON s.resort_id = r.id
            WHERE s.date = (
                SELECT MAX(date) FROM snow_data WHERE resort_id = s.resort_id
            )
            ORDER BY r.country, r.name
        """)

        rows = cursor.fetchall()

        if not rows:
            print("No data to export.")
            return

        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'Resort Name', 'Country', 'Region',
                'Base Elevation (m)', 'Summit Elevation (m)',
                'Date', 'Base Depth (cm)', 'Summit Depth (cm)',
                '24h Snow (cm)', '48h Snow (cm)', '7-Day Snow (cm)',
                'Season Total (cm)', 'Lifts Open', 'Total Lifts',
                'Runs Open', 'Total Runs', 'Temperature (°C)',
                'Weather', 'Scraped At'
            ])

            # Data rows
            for row in rows:
                writer.writerow(list(row))

        print(f"Exported {len(rows)} resorts to {output_file}")
        conn.close()

    def export_historical_to_csv(self, resort_name: str, output_file: str, days: int = 30):
        """Export historical data for a specific resort."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days)).date()

        cursor.execute("""
            SELECT
                r.name,
                s.date,
                s.snow_depth_base_cm,
                s.snow_depth_summit_cm,
                s.new_snow_24h_cm,
                s.new_snow_48h_cm,
                s.new_snow_7d_cm,
                s.lifts_open,
                s.lifts_total,
                s.runs_open,
                s.runs_total,
                s.temperature_base_c,
                s.weather_condition
            FROM snow_data s
            JOIN resorts r ON s.resort_id = r.id
            WHERE r.name = ? AND s.date >= ?
            ORDER BY s.date DESC
        """, (resort_name, cutoff_date))

        rows = cursor.fetchall()

        if not rows:
            print(f"No historical data found for {resort_name}")
            return

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            writer.writerow([
                'Resort', 'Date', 'Base Depth (cm)', 'Summit Depth (cm)',
                '24h Snow (cm)', '48h Snow (cm)', '7-Day Snow (cm)',
                'Lifts Open', 'Total Lifts', 'Runs Open', 'Total Runs',
                'Temperature (°C)', 'Weather'
            ])

            for row in rows:
                writer.writerow(list(row))

        print(f"Exported {len(rows)} days of data for {resort_name} to {output_file}")
        conn.close()

    def export_to_json(self, output_file: str = "ski_resort_data.json"):
        """Export all data to JSON format."""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get all resorts
        cursor.execute("SELECT * FROM resorts ORDER BY name")
        resorts = [dict(row) for row in cursor.fetchall()]

        # Get latest snow data for each resort
        for resort in resorts:
            cursor.execute("""
                SELECT * FROM snow_data
                WHERE resort_id = ?
                ORDER BY date DESC
                LIMIT 30
            """, (resort['id'],))

            resort['snow_data'] = [dict(row) for row in cursor.fetchall()]

        # Write to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(resorts, f, indent=2, default=str)

        print(f"Exported data for {len(resorts)} resorts to {output_file}")
        conn.close()

    def generate_powder_report(self, min_snowfall: int = 10):
        """Generate a report of resorts with significant fresh snow."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                r.name,
                r.country,
                r.region,
                s.new_snow_24h_cm,
                s.new_snow_48h_cm,
                s.snow_depth_base_cm,
                s.date
            FROM snow_data s
            JOIN resorts r ON s.resort_id = r.id
            WHERE s.date >= date('now', '-2 days')
                AND (s.new_snow_24h_cm >= ? OR s.new_snow_48h_cm >= ?)
            ORDER BY s.new_snow_24h_cm DESC
        """, (min_snowfall, min_snowfall * 1.5))

        rows = cursor.fetchall()

        print("\n" + "=" * 70)
        print(f"POWDER ALERT - Resorts with {min_snowfall}+ cm Fresh Snow")
        print("=" * 70)

        if not rows:
            print(f"No resorts found with {min_snowfall}+ cm of fresh snow recently.")
        else:
            for row in rows:
                print(f"\n{row['name']} ({row['region']}, {row['country']})")
                print(f"  24h Snowfall: {row['new_snow_24h_cm']} cm")
                if row['new_snow_48h_cm']:
                    print(f"  48h Snowfall: {row['new_snow_48h_cm']} cm")
                if row['snow_depth_base_cm']:
                    print(f"  Base Depth: {row['snow_depth_base_cm']} cm")
                print(f"  Date: {row['date']}")

        print("\n" + "=" * 70)
        conn.close()

    def generate_stats_report(self):
        """Generate summary statistics."""
        conn = self.get_connection()
        cursor = conn.cursor()

        print("\n" + "=" * 70)
        print("SKI RESORT DATABASE STATISTICS")
        print("=" * 70)

        # Total resorts
        cursor.execute("SELECT COUNT(*) as count FROM resorts")
        total_resorts = cursor.fetchone()['count']
        print(f"\nTotal Resorts in Database: {total_resorts}")

        # Resorts by country
        cursor.execute("""
            SELECT country, COUNT(*) as count
            FROM resorts
            GROUP BY country
            ORDER BY count DESC
        """)
        print("\nResorts by Country:")
        for row in cursor.fetchall():
            print(f"  {row['country']}: {row['count']}")

        # Latest scraping stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_attempts,
                SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
                MAX(scrape_time) as last_scrape
            FROM scraping_log
            WHERE DATE(scrape_time) = DATE('now')
        """)
        scrape_stats = cursor.fetchone()
        if scrape_stats['total_attempts']:
            print(f"\nToday's Scraping Activity:")
            print(f"  Total Attempts: {scrape_stats['total_attempts']}")
            print(f"  Successful: {scrape_stats['successful']}")
            print(f"  Success Rate: {scrape_stats['successful']/scrape_stats['total_attempts']*100:.1f}%")
            print(f"  Last Scrape: {scrape_stats['last_scrape']}")

        # Top snowfall in last 24h
        cursor.execute("""
            SELECT r.name, s.new_snow_24h_cm
            FROM snow_data s
            JOIN resorts r ON s.resort_id = r.id
            WHERE s.date >= date('now', '-1 day')
                AND s.new_snow_24h_cm IS NOT NULL
            ORDER BY s.new_snow_24h_cm DESC
            LIMIT 5
        """)
        print("\nTop 5 Resorts - 24h Snowfall:")
        for i, row in enumerate(cursor.fetchall(), 1):
            print(f"  {i}. {row['name']}: {row['new_snow_24h_cm']} cm")

        # Deepest base
        cursor.execute("""
            SELECT r.name, s.snow_depth_base_cm
            FROM snow_data s
            JOIN resorts r ON s.resort_id = r.id
            WHERE s.date >= date('now', '-1 day')
                AND s.snow_depth_base_cm IS NOT NULL
            ORDER BY s.snow_depth_base_cm DESC
            LIMIT 5
        """)
        print("\nTop 5 Resorts - Base Depth:")
        for i, row in enumerate(cursor.fetchall(), 1):
            print(f"  {i}. {row['name']}: {row['snow_depth_base_cm']} cm")

        print("\n" + "=" * 70)
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Export ski resort snow data',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--csv', action='store_true',
                       help='Export latest data to CSV')
    parser.add_argument('--json', action='store_true',
                       help='Export all data to JSON')
    parser.add_argument('--historical', type=str, metavar='RESORT',
                       help='Export historical data for specific resort')
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days for historical export (default: 30)')
    parser.add_argument('--powder', action='store_true',
                       help='Show powder alert report')
    parser.add_argument('--min-snow', type=int, default=10,
                       help='Minimum snowfall for powder alert (cm, default: 10)')
    parser.add_argument('--stats', action='store_true',
                       help='Show database statistics')
    parser.add_argument('--output', type=str,
                       help='Output filename (default: auto-generated)')

    args = parser.parse_args()

    exporter = DataExporter()

    if args.csv:
        output = args.output or 'latest_snow_data.csv'
        exporter.export_latest_to_csv(output)

    if args.json:
        output = args.output or 'ski_resort_data.json'
        exporter.export_to_json(output)

    if args.historical:
        output = args.output or f"{args.historical.replace(' ', '_')}_history.csv"
        exporter.export_historical_to_csv(args.historical, output, args.days)

    if args.powder:
        exporter.generate_powder_report(args.min_snow)

    if args.stats:
        exporter.generate_stats_report()

    if not any([args.csv, args.json, args.historical, args.powder, args.stats]):
        parser.print_help()


if __name__ == '__main__':
    main()
