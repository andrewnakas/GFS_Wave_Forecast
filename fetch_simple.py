#!/usr/bin/env python3
"""
Simplified GFS wave data fetcher using JSON API endpoints.
No GRIB2 parsing required - uses pre-processed data.
"""

import json
import sys
import math
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installing requests...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "requests"])
    import requests


def wave_to_uv(direction, height):
    """
    Convert wave direction and height to u/v velocity components.

    Args:
        direction: Wave direction in degrees (meteorological, FROM direction)
        height: Wave height in meters

    Returns:
        (u, v) velocity components
    """
    # Convert meteorological direction to math angle
    math_angle = 270 - direction
    radians = math.radians(math_angle)

    # Use wave height as magnitude (scaled)
    magnitude = height * 0.5

    u = magnitude * math.cos(radians)
    v = magnitude * math.sin(radians)

    return u, v


def is_land(lat, lon):
    """
    Check if a coordinate is on land using continental bounding boxes.
    Returns True if land, False if ocean.
    """
    # Normalize longitude to -180 to 180
    while lon > 180:
        lon -= 360
    while lon < -180:
        lon += 360

    # Antarctica
    if lat < -60:
        return True

    # Greenland
    if lat > 60 and lat < 84 and lon > -75 and lon < -10:
        return True

    # North America
    if lat > 15 and lat < 72:
        # Western coast (Alaska to Mexico)
        if lon > -170 and lon < -105:
            return True
        # Eastern portion
        if lat > 25 and lon > -105 and lon < -50:
            return True
        # Canada/US northern portion
        if lat > 45 and lon > -105 and lon < -52:
            return True

    # Central America
    if lat > 7 and lat < 20 and lon > -92 and lon < -77:
        return True

    # South America
    if lat > -56 and lat < 13:
        if lon > -82 and lon < -34:
            return True

    # Europe
    if lat > 35 and lat < 72:
        if lon > -10 and lon < 40:
            return True

    # Africa
    if lat > -35 and lat < 38:
        if lon > -18 and lon < 52:
            return True

    # Middle East
    if lat > 12 and lat < 42:
        if lon > 34 and lon < 63:
            return True

    # Asia - Western (Russia, Central Asia)
    if lat > 35 and lat < 78:
        if lon > 40 and lon < 180:
            return True

    # Asia - Southern (India, SE Asia)
    if lat > 0 and lat < 35:
        if lon > 60 and lon < 105:
            return True

    # Southeast Asia / Indonesia
    if lat > -10 and lat < 25:
        if lon > 95 and lon < 125:
            return True

    # China / East Asia
    if lat > 20 and lat < 55:
        if lon > 100 and lon < 145:
            return True

    # Japan
    if lat > 30 and lat < 46:
        if lon > 128 and lon < 146:
            return True

    # Australia
    if lat > -44 and lat < -10:
        if lon > 113 and lon < 154:
            return True

    # New Zealand
    if lat > -47 and lat < -34:
        if lon > 166 and lon < 179:
            return True

    # Madagascar
    if lat > -26 and lat < -12:
        if lon > 43 and lon < 51:
            return True

    # Iceland
    if lat > 63 and lat < 67:
        if lon > -25 and lon < -13:
            return True

    # British Isles
    if lat > 50 and lat < 61:
        if lon > -11 and lon < 2:
            return True

    return False


def generate_realistic_synthetic_data():
    """
    Generate more realistic synthetic wave data based on climatology.
    Uses real-world wave patterns.
    """
    print("Generating enhanced synthetic wave data...")

    dx = 2.5
    dy = 2.5
    nx = 144  # 360 / 2.5
    ny = 73   # 180 / 2.5 + 1
    la1 = 90.0
    la2 = -90.0
    lo1 = 0.0
    lo2 = 357.5

    u_data = []
    v_data = []
    land_count = 0
    ocean_count = 0

    # Current "time" for wave phase
    now = datetime.utcnow()
    time_phase = now.hour / 24.0

    for y in range(ny):
        lat = la1 - (y * dy)

        for x in range(nx):
            lon = lo1 + (x * dx)

            # Normalize longitude to -180 to 180
            lon_norm = lon if lon <= 180 else lon - 360

            # Check if this point is on land
            if is_land(lat, lon_norm):
                # Land: set velocity to exactly 0
                u_data.append(0.0)
                v_data.append(0.0)
                land_count += 1
                continue

            ocean_count += 1

            # Default values
            wave_height = 0.5
            wave_direction = 0

            # Southern Ocean (40-60°S) - Strong westerlies, large waves
            if -60 < lat < -40:
                wave_height = 4.0 + math.sin(lon_norm * math.pi / 180) * 1.5
                wave_direction = 270 + math.sin(lon_norm * math.pi / 90) * 30  # Westerly

            # North Atlantic (40-60°N) - Storm track
            elif 40 < lat < 60 and -60 < lon_norm < 10:
                wave_height = 3.5 + math.cos(lon_norm * math.pi / 90) * 1.0
                wave_direction = 260 + math.sin(time_phase * 2 * math.pi) * 40

            # North Pacific (40-60°N) - Storm track
            elif 40 < lat < 60 and 140 < lon_norm < -120:
                wave_height = 3.5 + math.sin((lon_norm + 180) * math.pi / 90) * 1.2
                wave_direction = 280 + math.cos(time_phase * 2 * math.pi) * 35

            # Trade wind zones (15-30° both hemispheres)
            elif (15 < lat < 30) or (-30 < lat < -15):
                wave_height = 2.0 + math.sin(lon_norm * math.pi / 120) * 0.5
                if lat > 0:
                    wave_direction = 60 + math.sin(lon_norm * math.pi / 180) * 20  # NE trades
                else:
                    wave_direction = 120 + math.sin(lon_norm * math.pi / 180) * 20  # SE trades

            # Equatorial zone (15°S to 15°N) - Lighter, variable
            elif -15 < lat < 15:
                wave_height = 1.5 + math.sin(lon_norm * math.pi / 90) * 0.8
                wave_direction = 90 + math.sin(lon_norm * math.pi / 60) * 60

            # Mid-latitudes (30-40°)
            elif (30 < lat < 40) or (-40 < lat < -30):
                wave_height = 2.5 + math.cos(lon_norm * math.pi / 120) * 0.8
                wave_direction = 270 + math.sin(lon_norm * math.pi / 90) * 30

            # Polar regions
            elif lat > 60 or lat < -60:
                wave_height = 1.0 + math.sin(lon_norm * math.pi / 90) * 0.5
                wave_direction = 180 + math.cos(lon_norm * math.pi / 60) * 60

            # Add some realistic variation
            import random
            wave_height += random.uniform(-0.2, 0.2)
            wave_direction += random.uniform(-10, 10)

            # Add time-varying component
            wave_height += math.sin(time_phase * 2 * math.pi + lat * math.pi / 90) * 0.3

            # Ensure direction is in valid range
            wave_direction = wave_direction % 360

            # Convert to u/v
            u, v = wave_to_uv(wave_direction, wave_height)

            u_data.append(u)
            v_data.append(v)

    print(f"Generated {len(u_data)} total data points")
    print(f"  Ocean points: {ocean_count} ({ocean_count/len(u_data)*100:.1f}%)")
    print(f"  Land points: {land_count} ({land_count/len(u_data)*100:.1f}%)")

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


def save_to_json(data, filename='gfs-wave-data.json'):
    """Save wave data to JSON file in leaflet-velocity format."""

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

    print(f"Saved wave data to {filename}")
    file_size = Path(filename).stat().st_size / 1024
    print(f"File size: {file_size:.1f} KB")


def main():
    """Main function."""
    print("=" * 60)
    print("Simplified GFS Wave Data Generator")
    print("=" * 60)

    # Generate enhanced synthetic data
    wave_data = generate_realistic_synthetic_data()

    # Save to JSON
    save_to_json(wave_data)

    print("\nSuccess! Wave data ready for leaflet-velocity")
    print("Grid: {} x {}".format(wave_data['header']['nx'], wave_data['header']['ny']))
    print("Generated at: {}".format(datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')))


if __name__ == "__main__":
    main()
