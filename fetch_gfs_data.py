#!/usr/bin/env python3
"""
Fetch GFS wave forecast data and convert to leaflet-velocity JSON format.
Requires: xarray, cfgrib, requests, numpy
Install: pip install xarray cfgrib requests numpy
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import requests
import numpy as np

try:
    import xarray as xr
except ImportError:
    print("Error: xarray not installed. Run: pip install xarray cfgrib requests numpy")
    sys.exit(1)


def get_latest_gfs_cycle():
    """Get the latest available GFS cycle."""
    now = datetime.utcnow()

    # GFS runs at 00, 06, 12, 18 UTC
    # Data is usually available 4-5 hours after cycle time
    cycle_hour = (now.hour // 6) * 6
    cycle_time = now.replace(hour=cycle_hour, minute=0, second=0, microsecond=0)

    # If current time is less than 4 hours after cycle, use previous cycle
    if (now - cycle_time).total_seconds() < 4 * 3600:
        cycle_time -= timedelta(hours=6)

    return cycle_time


def fetch_gfs_wave_data(cycle_time, forecast_hour=0):
    """
    Fetch GFS wave data from NOAA NOMADS server.

    Parameters:
    - cycle_time: datetime object for the forecast cycle
    - forecast_hour: forecast hour (0, 3, 6, ..., 384)

    Returns:
    - Dictionary with wave data
    """
    print(f"Fetching GFS wave data for {cycle_time} +{forecast_hour}h...")

    # Format cycle time
    date_str = cycle_time.strftime('%Y%m%d')
    cycle_str = cycle_time.strftime('%H')
    fhr_str = f"{forecast_hour:03d}"

    # Build URL for GFS wave GRIB2 file
    # Using the 0.25 degree global wave model
    base_url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod"
    filename = f"gfswave.t{cycle_str}z.global.0p25.f{fhr_str}.grib2"
    url = f"{base_url}/gfs.{date_str}/{cycle_str}/wave/gridded/{filename}"

    print(f"URL: {url}")

    # Download the file
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        # Save to temporary file
        temp_file = Path(f"/tmp/gfs_wave_{date_str}_{cycle_str}_f{fhr_str}.grib2")
        temp_file.write_bytes(response.content)

        print(f"Downloaded {len(response.content)} bytes")

        return parse_grib_file(temp_file)

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")

        # Try alternative URL (AWS mirror)
        alt_url = f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{date_str}/{cycle_str}/wave/gridded/{filename}"
        print(f"Trying alternative URL: {alt_url}")

        try:
            response = requests.get(alt_url, timeout=60)
            response.raise_for_status()
            temp_file = Path(f"/tmp/gfs_wave_{date_str}_{cycle_str}_f{fhr_str}.grib2")
            temp_file.write_bytes(response.content)
            return parse_grib_file(temp_file)
        except Exception as e2:
            print(f"Error with alternative URL: {e2}")
            return None


def parse_grib_file(grib_file):
    """Parse GRIB2 file and extract wave data."""
    print(f"Parsing GRIB file: {grib_file}")

    try:
        # Open with xarray and cfgrib
        ds = xr.open_dataset(
            grib_file,
            engine='cfgrib',
            backend_kwargs={'filter_by_keys': {'typeOfLevel': 'surface'}}
        )

        print("Available variables:", list(ds.data_vars))

        # Extract wave parameters
        # HTSGW: Significant Height of Combined Wind Waves and Swell
        # DIRPW: Primary Wave Direction
        # PERPW: Primary Wave Mean Period

        wave_height = ds['swh'].values if 'swh' in ds else None  # significant wave height
        wave_direction = ds['mwd'].values if 'mwd' in ds else None  # mean wave direction
        wave_period = ds['mwp'].values if 'mwp' in ds else None  # mean wave period

        lats = ds['latitude'].values
        lons = ds['longitude'].values

        # Convert to u/v components
        if wave_height is not None and wave_direction is not None:
            u, v = wave_to_uv(wave_direction, wave_height)

            return {
                'u': u,
                'v': v,
                'lats': lats,
                'lons': lons,
                'wave_height': wave_height,
                'wave_direction': wave_direction,
                'wave_period': wave_period
            }
        else:
            print("Error: Required wave parameters not found in GRIB file")
            return None

    except Exception as e:
        print(f"Error parsing GRIB file: {e}")
        return None


def wave_to_uv(direction, height):
    """
    Convert wave direction and height to u/v velocity components.

    Parameters:
    - direction: wave direction in degrees (meteorological convention)
    - height: significant wave height in meters

    Returns:
    - u, v: velocity components
    """
    # Convert meteorological direction (direction FROM) to math angle
    # Meteorological: 0° = North, clockwise
    # Mathematical: 0° = East, counterclockwise
    math_angle = 270 - direction
    radians = np.deg2rad(math_angle)

    # Use wave height as magnitude (scaled)
    magnitude = height * 0.5

    u = magnitude * np.cos(radians)
    v = magnitude * np.sin(radians)

    return u, v


def convert_to_leaflet_velocity_format(data):
    """Convert wave data to leaflet-velocity JSON format."""

    lats = data['lats']
    lons = data['lons']
    u = data['u']
    v = data['v']

    # Get grid parameters
    lat_sorted = np.sort(lats)[::-1]  # North to south
    lon_sorted = np.sort(lons)

    la1 = float(lat_sorted[0])
    la2 = float(lat_sorted[-1])
    lo1 = float(lon_sorted[0])
    lo2 = float(lon_sorted[-1])

    ny = len(lat_sorted)
    nx = len(lon_sorted)

    dy = abs(lat_sorted[0] - lat_sorted[1]) if len(lat_sorted) > 1 else 0.25
    dx = abs(lon_sorted[1] - lon_sorted[0]) if len(lon_sorted) > 1 else 0.25

    # Flatten to 1D arrays (north to south, west to east)
    u_flat = u.flatten().tolist()
    v_flat = v.flatten().tolist()

    # Create leaflet-velocity format
    result = [
        {
            "header": {
                "parameterCategory": 2,
                "parameterNumber": 2,
                "dx": float(dx),
                "dy": float(dy),
                "nx": int(nx),
                "ny": int(ny),
                "la1": float(la1),
                "la2": float(la2),
                "lo1": float(lo1),
                "lo2": float(lo2)
            },
            "data": u_flat
        },
        {
            "header": {
                "parameterCategory": 2,
                "parameterNumber": 3,
                "dx": float(dx),
                "dy": float(dy),
                "nx": int(nx),
                "ny": int(ny),
                "la1": float(la1),
                "la2": float(la2),
                "lo1": float(lo1),
                "lo2": float(lo2)
            },
            "data": v_flat
        }
    ]

    return result


def main():
    """Main function."""
    # Get latest cycle
    cycle_time = get_latest_gfs_cycle()
    print(f"Using GFS cycle: {cycle_time}")

    # Fetch data for current analysis (f000)
    wave_data = fetch_gfs_wave_data(cycle_time, forecast_hour=0)

    if wave_data is None:
        print("Failed to fetch GFS data")
        sys.exit(1)

    # Convert to leaflet-velocity format
    velocity_data = convert_to_leaflet_velocity_format(wave_data)

    # Save to JSON file
    output_file = Path("gfs-wave-data.json")
    with open(output_file, 'w') as f:
        json.dump(velocity_data, f)

    print(f"Saved wave data to {output_file}")
    print(f"Grid size: {velocity_data[0]['header']['nx']} x {velocity_data[0]['header']['ny']}")
    print(f"Data points: {len(velocity_data[0]['data'])}")


if __name__ == "__main__":
    main()
