#!/usr/bin/env python3
"""
Real GFS Wave Data Fetcher from NOAA NOMADS
Downloads actual wave forecast data from NOAA's operational models.
"""

import json
import sys
import math
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installing requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "requests"])
    import requests


def get_latest_gfs_cycle():
    """
    Determine the latest available GFS cycle.
    GFS runs 4 times a day: 00z, 06z, 12z, 18z
    Data is typically available 3-4 hours after cycle time.
    """
    now = datetime.utcnow()

    # GFS cycles
    cycles = [0, 6, 12, 18]

    # Find the most recent cycle that should be available
    # Subtract 4 hours to account for processing time
    adjusted_time = now - timedelta(hours=4)

    current_hour = adjusted_time.hour
    latest_cycle = max([c for c in cycles if c <= current_hour], default=18)

    # If we're early in the day and no cycle is available, use previous day's last cycle
    if current_hour < 4:
        cycle_date = (adjusted_time - timedelta(days=1)).strftime('%Y%m%d')
        cycle_hour = '18'
    else:
        cycle_date = adjusted_time.strftime('%Y%m%d')
        cycle_hour = f'{latest_cycle:02d}'

    return cycle_date, cycle_hour


def download_grib_data(cycle_date, cycle_hour, forecast_hour='000'):
    """
    Download wave data from NOAA NOMADS using the simpler global wave model.
    Uses the 0.25 degree global wave forecast.
    """
    # Try different NOAA data sources
    sources = [
        # Primary source - latest production data
        f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{cycle_date}/{cycle_hour}/wave/gridded/gfswave.t{cycle_hour}z.global.0p25.f{forecast_hour}.grib2",
        # Backup - try 0.16 degree resolution
        f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{cycle_date}/{cycle_hour}/wave/gridded/gfswave.t{cycle_hour}z.global.0p16.f{forecast_hour}.grib2",
        # FTP fallback
        f"ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{cycle_date}/{cycle_hour}/wave/gridded/gfswave.t{cycle_hour}z.global.0p25.f{forecast_hour}.grib2",
    ]

    print(f"Attempting to download GFS wave data for cycle {cycle_date} {cycle_hour}Z...")

    for url in sources:
        try:
            print(f"Trying: {url}")
            response = requests.get(url, timeout=60, stream=True)

            if response.status_code == 200:
                print(f"✓ Successfully accessed data from NOMADS")
                return response.content, url
            else:
                print(f"  Status code: {response.status_code}")
        except Exception as e:
            print(f"  Error: {str(e)}")
            continue

    return None, None


def try_parse_with_cfgrib(grib_file):
    """Try parsing GRIB file with cfgrib/xarray."""
    try:
        import xarray as xr
        import cfgrib

        print("Using cfgrib to parse GRIB2 data...")

        # Open with cfgrib engine
        ds = xr.open_dataset(
            grib_file,
            engine='cfgrib',
            backend_kwargs={'filter_by_keys': {'stepType': 'instant'}}
        )

        # Extract wave parameters
        # Common variable names in GFS wave files
        var_mappings = {
            'swh': 'Significant Wave Height',
            'htsgw': 'Significant Wave Height',
            'perpw': 'Primary Wave Period',
            'dirpw': 'Primary Wave Direction',
            'u': 'U-component',
            'v': 'V-component'
        }

        wave_height = None
        wave_direction = None

        # Try to find wave height
        for var in ['swh', 'htsgw', 'HTSGW', 'SWH']:
            if var in ds:
                wave_height = ds[var].values
                print(f"  Found wave height: {var}")
                break

        # Try to find wave direction
        for var in ['dirpw', 'DIRPW', 'mwd', 'MWD']:
            if var in ds:
                wave_direction = ds[var].values
                print(f"  Found wave direction: {var}")
                break

        if wave_height is not None and wave_direction is not None:
            lats = ds.latitude.values if 'latitude' in ds else ds.lat.values
            lons = ds.longitude.values if 'longitude' in ds else ds.lon.values

            return {
                'wave_height': wave_height,
                'wave_direction': wave_direction,
                'lats': lats,
                'lons': lons,
                'method': 'cfgrib'
            }

        # List available variables
        print(f"Available variables: {list(ds.variables.keys())}")

    except ImportError:
        print("cfgrib not available")
    except Exception as e:
        print(f"cfgrib error: {e}")

    return None


def try_parse_with_pygrib(grib_file):
    """Try parsing GRIB file with pygrib."""
    try:
        import pygrib

        print("Using pygrib to parse GRIB2 data...")

        grbs = pygrib.open(grib_file)

        wave_height = None
        wave_direction = None
        lats = None
        lons = None

        # Iterate through all messages to find wave parameters
        for grb in grbs:
            name = grb.name
            print(f"  Found: {name}")

            if 'Significant height' in name or 'wave height' in name.lower():
                wave_height = grb.values
                lats, lons = grb.latlons()
                print(f"    ✓ Extracted wave height")

            if 'direction' in name.lower() and 'wave' in name.lower():
                wave_direction = grb.values
                print(f"    ✓ Extracted wave direction")

        grbs.close()

        if wave_height is not None and wave_direction is not None:
            return {
                'wave_height': wave_height,
                'wave_direction': wave_direction,
                'lats': lats,
                'lons': lons,
                'method': 'pygrib'
            }

    except ImportError:
        print("pygrib not available")
    except Exception as e:
        print(f"pygrib error: {e}")

    return None


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

    # Use wave height as magnitude (scaled for visualization)
    magnitude = height * 0.5

    u = magnitude * math.cos(radians)
    v = magnitude * math.sin(radians)

    return u, v


def convert_to_leaflet_format(data):
    """Convert parsed GRIB data to leaflet-velocity JSON format."""
    import numpy as np

    wave_height = data['wave_height']
    wave_direction = data['wave_direction']
    lats = data['lats']
    lons = data['lons']

    print(f"\nProcessing wave data...")
    print(f"  Data shape: {wave_height.shape}")
    print(f"  Lat range: {lats.min():.2f} to {lats.max():.2f}")
    print(f"  Lon range: {lons.min():.2f} to {lons.max():.2f}")

    # Handle NaN values when reporting stats
    valid_heights = wave_height[~np.isnan(wave_height)]
    if len(valid_heights) > 0:
        print(f"  Wave height range: {valid_heights.min():.2f} to {valid_heights.max():.2f} m")
        print(f"  Valid ocean points: {len(valid_heights):,} ({100*len(valid_heights)/wave_height.size:.1f}%)")
    else:
        print(f"  Warning: No valid wave height data found")

    # Determine grid parameters
    if len(wave_height.shape) == 2:
        ny, nx = wave_height.shape
    else:
        # Flatten if needed
        wave_height = wave_height.reshape(-1)
        wave_direction = wave_direction.reshape(-1)
        lats = lats.reshape(-1)
        lons = lons.reshape(-1)
        ny, nx = 1, len(wave_height)

    # Calculate grid spacing
    if len(lats.shape) == 2:
        lat_1d = lats[:, 0]
        lon_1d = lons[0, :]
    else:
        # Assume regular grid
        lat_1d = sorted(set(lats.flatten()))
        lon_1d = sorted(set(lons.flatten()))

    dy = abs(lat_1d[1] - lat_1d[0]) if len(lat_1d) > 1 else 2.5
    dx = abs(lon_1d[1] - lon_1d[0]) if len(lon_1d) > 1 else 2.5

    la1 = float(lat_1d[0])
    la2 = float(lat_1d[-1])
    lo1 = float(lon_1d[0])
    lo2 = float(lon_1d[-1])

    # Convert to u/v components
    u_data = []
    v_data = []

    flat_height = wave_height.flatten()
    flat_direction = wave_direction.flatten()

    for h, d in zip(flat_height, flat_direction):
        # Skip NaN values (land areas) - set to 0
        if np.isnan(h) or np.isnan(d):
            u_data.append(0.0)
            v_data.append(0.0)
        else:
            u, v = wave_to_uv(d, h)
            u_data.append(float(u))
            v_data.append(float(v))

    print(f"  Converted to {len(u_data)} grid points")

    return {
        'header': {
            'dx': float(dx),
            'dy': float(dy),
            'nx': int(nx),
            'ny': int(ny),
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

    print(f"\n✓ Saved wave data to {filename}")
    file_size = Path(filename).stat().st_size / 1024
    print(f"  File size: {file_size:.1f} KB")


def main():
    """Main function."""
    print("=" * 60)
    print("NOAA GFS Wave Data Downloader")
    print("=" * 60)

    # Get latest available cycle
    cycle_date, cycle_hour = get_latest_gfs_cycle()
    print(f"\nTarget cycle: {cycle_date} {cycle_hour}Z")

    # Download GRIB2 data
    grib_data, url = download_grib_data(cycle_date, cycle_hour)

    if grib_data is None:
        print("\n❌ Failed to download GRIB data from all sources")
        print("   This could be because:")
        print("   - The latest cycle is not yet available")
        print("   - Network issues")
        print("   - NOMADS server is down")
        print("\n   Try again in a few minutes, or check https://nomads.ncep.noaa.gov/")
        sys.exit(1)

    # Save to temporary file
    temp_grib = 'temp_wave_data.grib2'
    with open(temp_grib, 'wb') as f:
        f.write(grib_data)

    print(f"\n✓ Downloaded {len(grib_data) / 1024 / 1024:.1f} MB")
    print(f"  Source: {url}")

    # Try to parse with available libraries
    print("\nParsing GRIB2 file...")

    parsed_data = try_parse_with_cfgrib(temp_grib)
    if parsed_data is None:
        parsed_data = try_parse_with_pygrib(temp_grib)

    if parsed_data is None:
        print("\n❌ Could not parse GRIB2 file")
        print("   Please install one of these libraries:")
        print("   - pip install cfgrib xarray")
        print("   - pip install pygrib")
        os.remove(temp_grib)
        sys.exit(1)

    print(f"\n✓ Successfully parsed with {parsed_data['method']}")

    # Convert to leaflet format
    wave_data = convert_to_leaflet_format(parsed_data)

    # Save to JSON
    save_to_json(wave_data)

    # Clean up
    os.remove(temp_grib)

    print("\n" + "=" * 60)
    print("SUCCESS! Real GFS wave data ready for leaflet-velocity")
    print("=" * 60)
    print(f"Grid: {wave_data['header']['nx']} x {wave_data['header']['ny']}")
    print(f"Cycle: {cycle_date} {cycle_hour}Z")
    print(f"Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
