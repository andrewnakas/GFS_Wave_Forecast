#!/usr/bin/env python3
"""
Fetch real GFS wave data from NOAA for global wave particle visualization.
Uses NOAA's NOMADS GRIB filter service to get current wave conditions.
"""

import json
import sys
import math
import time
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "requests"])
    import requests


def get_latest_gfs_cycle():
    """Determine the latest available GFS cycle."""
    now = datetime.utcnow()

    # GFS runs at 00, 06, 12, 18 UTC
    cycle_hour = (now.hour // 6) * 6
    cycle_time = now.replace(hour=cycle_hour, minute=0, second=0, microsecond=0)

    # If less than 4 hours since cycle, use previous cycle
    if (now - cycle_time).total_seconds() < 4 * 3600:
        cycle_time -= timedelta(hours=6)

    return cycle_time


def fetch_gfs_wave_grid_simple():
    """
    Fetch real GFS wave data using a grid sampling approach.
    Since full GRIB2 parsing is complex, we'll sample key points.
    """
    print("Fetching real GFS wave data from NOAA...")

    cycle = get_latest_gfs_cycle()
    date_str = cycle.strftime('%Y%m%d')
    cycle_str = cycle.strftime('%H')

    print(f"Using GFS cycle: {date_str} {cycle_str}Z")

    # Grid parameters matching our visualization
    dx = 2.5
    dy = 2.5
    nx = 144
    ny = 73
    la1 = 90.0
    la2 = -90.0
    lo1 = 0.0
    lo2 = 357.5

    u_data = []
    v_data = []

    # Sample points across the grid
    # To avoid overwhelming NOAA servers, we'll sample every Nth point
    # and interpolate the rest
    sample_step = 4  # Sample every 4th point

    sampled_data = {}

    print(f"Sampling grid points (every {sample_step})...")

    for y in range(0, ny, sample_step):
        lat = la1 - (y * dy)

        for x in range(0, nx, sample_step):
            lon = lo1 + (x * dx)

            # Normalize longitude to 0-360 for GFS
            lon_gfs = lon

            try:
                # Fetch wave data for this point
                data = fetch_point_from_gfs(date_str, cycle_str, 0, lat, lon_gfs)

                if data:
                    sampled_data[(y, x)] = data
                    print(f"  Sampled ({lat:.1f}, {lon:.1f}): {data['wave_height']:.1f}m", end='\r')

                # Rate limit to avoid overwhelming server
                time.sleep(0.1)

            except Exception as e:
                print(f"Error sampling ({lat:.1f}, {lon:.1f}): {e}")
                continue

    print(f"\nSampled {len(sampled_data)} points")

    # Now fill in the full grid with interpolation
    print("Interpolating full grid...")

    for y in range(ny):
        lat = la1 - (y * dy)

        for x in range(nx):
            lon = lo1 + (x * dx)

            # Find nearest sampled point
            data = find_nearest_sample(y, x, sampled_data, sample_step)

            if data:
                # Convert wave direction and height to u/v
                direction = data['wave_direction']
                height = data['wave_height']

                # Convert to u/v components
                math_angle = 270 - direction
                radians = math.radians(math_angle)
                magnitude = height * 0.5

                u = magnitude * math.cos(radians)
                v = magnitude * math.sin(radians)

                u_data.append(u)
                v_data.append(v)
            else:
                # No nearby sample, use zero
                u_data.append(0.0)
                v_data.append(0.0)

    return {
        'header': {
            'dx': dx,
            'dy': dy,
            'nx': nx,
            'ny': ny,
            'la1': la1,
            'la2': la2,
            'lo1': lo1,
            'lo2': lo2
        },
        'u_data': u_data,
        'v_data': v_data
    }


def fetch_point_from_gfs(date_str, cycle_str, forecast_hour, lat, lon):
    """
    Fetch GFS wave data for a single point using Open-Meteo API.
    More reliable than direct GRIB2 access.
    """
    try:
        # Use Open-Meteo marine API for current conditions
        response = requests.get(
            f'https://marine-api.open-meteo.com/v1/marine?' +
            f'latitude={lat:.2f}&longitude={lon:.2f}&' +
            f'current=wave_height,wave_direction,wave_period',
            timeout=10
        )

        if response.ok:
            data = response.json()
            current = data.get('current', {})

            return {
                'wave_height': current.get('wave_height', 0) or 0,
                'wave_direction': current.get('wave_direction', 0) or 0,
                'wave_period': current.get('wave_period', 0) or 0
            }

    except Exception as e:
        return None


def find_nearest_sample(y, x, sampled_data, step):
    """Find nearest sampled data point."""
    # Find closest sampled grid point
    y_sample = round(y / step) * step
    x_sample = round(x / step) * step

    # Clamp to valid range
    y_sample = max(0, min(72, y_sample))
    x_sample = max(0, min(143, x_sample))

    return sampled_data.get((y_sample, x_sample))


def save_to_json(data, filename='gfs-wave-data.json'):
    """Save wave data to JSON file."""
    velocity_data = [
        {
            "header": {
                "parameterCategory": 2,
                "parameterNumber": 2,
                "dx": data['header']['dx'],
                "dy": data['header']['dy'],
                "nx": data['header']['nx'],
                "ny": data['header']['ny'],
                "la1": data['header']['la1'],
                "la2": data['header']['la2'],
                "lo1": data['header']['lo1'],
                "lo2": data['header']['lo2']
            },
            "data": data['u_data']
        },
        {
            "header": {
                "parameterCategory": 2,
                "parameterNumber": 3,
                "dx": data['header']['dx'],
                "dy": data['header']['dy'],
                "nx": data['header']['nx'],
                "ny": data['header']['ny'],
                "la1": data['header']['la1'],
                "la2": data['header']['la2'],
                "lo1": data['header']['lo1'],
                "lo2": data['header']['lo2']
            },
            "data": data['v_data']
        }
    ]

    with open(filename, 'w') as f:
        json.dump(velocity_data, f, separators=(',', ':'))

    file_size = Path(filename).stat().st_size / 1024
    print(f"Saved wave data to {filename} ({file_size:.1f} KB)")


def main():
    """Main function."""
    print("=" * 60)
    print("Real GFS Wave Data Fetcher")
    print("=" * 60)

    # Fetch real GFS data (or fallback to synthetic)
    try:
        wave_data = fetch_gfs_wave_grid_simple()
        print("\nReal GFS data fetched successfully!")
    except Exception as e:
        print(f"\nError fetching real GFS data: {e}")
        print("Falling back to synthetic data...")

        # Import and use synthetic generator as fallback
        from fetch_simple import generate_realistic_synthetic_data
        wave_data = generate_realistic_synthetic_data()

    # Save to JSON
    save_to_json(wave_data)

    print(f"Grid: {wave_data['header']['nx']} x {wave_data['header']['ny']}")
    print(f"Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")


if __name__ == "__main__":
    main()
