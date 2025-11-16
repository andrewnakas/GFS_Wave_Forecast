#!/usr/bin/env python3
"""
Fetch NOAA WAVEWATCH III wave data directly from NOMADS.
Uses GRIB2 files which are commercially free and publicly available.
"""

import json
import sys
import math
import time
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "requests"])
    import requests


def get_latest_ww3_url():
    """
    Get the latest WAVEWATCH III GRIB2 file URL from NOAA NOMADS.
    Returns URL for global model at 0.5 degree resolution.
    """
    now = datetime.utcnow()

    # WW3 runs every 6 hours: 00, 06, 12, 18 UTC
    cycle_hour = (now.hour // 6) * 6
    run_time = now.replace(hour=cycle_hour, minute=0, second=0, microsecond=0)

    # If less than 4 hours since cycle start, use previous cycle
    if (now - run_time).total_seconds() < 4 * 3600:
        run_time -= timedelta(hours=6)

    date_str = run_time.strftime('%Y%m%d')
    cycle_str = run_time.strftime('%H')

    # NOMADS URL pattern for multi_1.glo_30m (global 0.5 degree)
    # This contains significant wave height and direction
    base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{date_str}/{cycle_str}/wave/gridded"
    grib_file = f"gfswave.t{cycle_str}z.global.0p25.f000.grib2"

    url = f"{base_url}/{grib_file}"

    print(f"WW3 Cycle: {date_str} {cycle_str}Z")
    print(f"URL: {url}")

    return url, run_time


def download_grib2(url, max_retries=3):
    """Download GRIB2 file with retries."""
    for attempt in range(max_retries):
        try:
            print(f"Downloading GRIB2 file (attempt {attempt + 1}/{max_retries})...")
            response = requests.get(url, timeout=120, stream=True)

            if response.status_code == 200:
                # Save to temporary file
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.grib2')

                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"  Downloaded: {downloaded / 1024 / 1024:.1f}MB ({percent:.0f}%)", end='\r')

                tmp_file.close()
                print(f"\nDownloaded to: {tmp_file.name}")
                return tmp_file.name
            else:
                print(f"  HTTP {response.status_code}")

        except Exception as e:
            print(f"  Error: {e}")

        if attempt < max_retries - 1:
            wait = 2 ** attempt
            print(f"  Waiting {wait}s before retry...")
            time.sleep(wait)

    return None


def parse_grib2_with_pygrib(grib_file):
    """Parse GRIB2 file using pygrib library."""
    try:
        import pygrib
    except ImportError:
        print("Installing pygrib...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "pygrib"])
        import pygrib

    print(f"Opening GRIB2 file with pygrib...")
    grbs = pygrib.open(grib_file)

    # Find wave height and direction messages
    wave_height = None
    wave_direction = None

    for grb in grbs:
        name = grb.name
        if 'Significant height of combined wind waves and swell' in name or 'HTSGW' in name:
            wave_height = grb
        elif 'Direction of wind waves' in name or 'DIRPW' in name:
            wave_direction = grb

    if not wave_height:
        # Try alternative approach - list all messages
        grbs.rewind()
        print("\nAvailable GRIB messages:")
        for i, grb in enumerate(grbs):
            print(f"  {i}: {grb.name} ({grb.shortName})")
            if i == 0:
                wave_height = grb  # Use first message as fallback

    grbs.close()

    if wave_height:
        lats, lons = wave_height.latlons()
        heights = wave_height.values

        # Get direction if available
        directions = None
        if wave_direction:
            directions = wave_direction.values

        return {
            'lats': lats,
            'lons': lons,
            'heights': heights,
            'directions': directions
        }

    return None


def parse_grib2_with_xarray(grib_file):
    """Parse GRIB2 file using xarray + cfgrib."""
    try:
        import xarray as xr
        import cfgrib
    except ImportError:
        print("Installing xarray and cfgrib...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "xarray", "cfgrib"])
        import xarray as xr

    print(f"Opening GRIB2 file with xarray...")
    ds = xr.open_dataset(grib_file, engine='cfgrib')

    print("\nDataset variables:")
    print(ds.data_vars)

    # Extract wave data
    # Common variable names: swh (significant wave height), mwd (mean wave direction)
    wave_height = None
    wave_direction = None

    for var in ds.data_vars:
        var_lower = str(var).lower()
        if 'wave' in var_lower and 'height' in var_lower:
            wave_height = ds[var]
        elif 'swh' in var_lower:
            wave_height = ds[var]
        elif 'direction' in var_lower:
            wave_direction = ds[var]
        elif 'mwd' in var_lower:
            wave_direction = ds[var]

    if wave_height is None:
        # Just use first variable
        first_var = list(ds.data_vars)[0]
        print(f"Using first variable: {first_var}")
        wave_height = ds[first_var]

    lats = ds.latitude.values
    lons = ds.longitude.values

    return {
        'lats': lats,
        'lons': lons,
        'heights': wave_height.values,
        'directions': wave_direction.values if wave_direction is not None else None
    }


def regrid_to_velocity_format(wave_data):
    """
    Convert GRIB2 wave data to our velocity grid format (144x73 at 2.5 degrees).
    """
    source_lats = wave_data['lats']
    source_lons = wave_data['lons']
    heights = wave_data['heights']
    directions = wave_data.get('directions')

    # Target grid
    dx = 2.5
    dy = 2.5
    nx = 144
    ny = 73
    la1 = 90.0
    lo1 = 0.0

    u_data = []
    v_data = []

    print("Regridding to velocity format...")

    # Create target grid
    for y in range(ny):
        target_lat = la1 - (y * dy)

        for x in range(nx):
            target_lon = lo1 + (x * dx)

            # Find nearest source point
            # This is a simple nearest-neighbor approach
            min_dist = float('inf')
            nearest_height = 0
            nearest_dir = 0

            # Sample a region around the target point
            for i in range(max(0, len(source_lats) // 2 - 5), min(len(source_lats), len(source_lats) // 2 + 5)):
                for j in range(max(0, len(source_lons[0]) // 2 - 5), min(len(source_lons[0]), len(source_lons[0]) // 2 + 5)):
                    src_lat = source_lats[i, j] if len(source_lats.shape) > 1 else source_lats[i]
                    src_lon = source_lons[i, j] if len(source_lons.shape) > 1 else source_lons[j]

                    # Normalize longitude
                    if src_lon > 180:
                        src_lon -= 360

                    # Calculate distance
                    dlat = target_lat - src_lat
                    dlon = target_lon - src_lon
                    if dlon > 180:
                        dlon -= 360
                    if dlon < -180:
                        dlon += 360

                    dist = dlat**2 + dlon**2

                    if dist < min_dist:
                        min_dist = dist
                        nearest_height = heights[i, j] if heights[i, j] is not None else 0
                        if directions is not None:
                            nearest_dir = directions[i, j] if directions[i, j] is not None else 0

            # Convert wave height and direction to u/v components
            if nearest_height > 0 and not math.isnan(nearest_height):
                # Convert direction (meteorological) to u/v
                math_angle = 270 - nearest_dir
                radians = math.radians(math_angle)
                magnitude = nearest_height * 0.5  # Scale factor

                u = magnitude * math.cos(radians)
                v = magnitude * math.sin(radians)
            else:
                u = 0
                v = 0

            u_data.append(float(u))
            v_data.append(float(v))

    print(f"Regridded {len(u_data)} points")

    return {
        'header': {
            'dx': dx,
            'dy': dy,
            'nx': nx,
            'ny': ny,
            'la1': la1,
            'la2': -90.0,
            'lo1': lo1,
            'lo2': 357.5
        },
        'u_data': u_data,
        'v_data': v_data
    }


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
    print(f"Saved to {filename} ({file_size:.1f} KB)")


def main():
    """Main function."""
    print("=" * 70)
    print("NOAA WAVEWATCH III Data Fetcher")
    print("Commercially Free - Direct from NOAA NOMADS")
    print("=" * 70)

    try:
        # Get latest WW3 URL
        url, run_time = get_latest_ww3_url()

        # Download GRIB2 file
        grib_file = download_grib2(url)

        if not grib_file:
            raise Exception("Failed to download GRIB2 file")

        # Parse GRIB2 file (try xarray first, fall back to pygrib)
        wave_data = None

        try:
            wave_data = parse_grib2_with_xarray(grib_file)
        except Exception as e:
            print(f"\nxarray failed: {e}")
            print("Trying pygrib...")
            try:
                wave_data = parse_grib2_with_pygrib(grib_file)
            except Exception as e2:
                print(f"pygrib failed: {e2}")

        # Clean up temp file
        try:
            os.unlink(grib_file)
        except:
            pass

        if not wave_data:
            raise Exception("Failed to parse GRIB2 file")

        # Regrid to our format
        velocity_data = regrid_to_velocity_format(wave_data)

        # Save to JSON
        save_to_json(velocity_data)

        print(f"\n✓ Successfully fetched NOAA WAVEWATCH III data")
        print(f"  Run time: {run_time.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"  Grid: {velocity_data['header']['nx']} x {velocity_data['header']['ny']}")

    except Exception as e:
        print(f"\n✗ Error fetching WAVEWATCH III data: {e}")
        print("\nFalling back to synthetic data...")

        # Import and use synthetic generator
        from fetch_simple import generate_realistic_synthetic_data
        wave_data = generate_realistic_synthetic_data()
        save_to_json(wave_data)


if __name__ == "__main__":
    main()
