#!/usr/bin/env python3
"""
GFS Wave Data Fetcher

This script fetches GFS Wave forecast data from NOAA's NOMADS server
and processes it into JSON format for web visualization.

Data source: NOAA GFS Wave (WAVEWATCH III)
Access: OpenDAP/THREDDS via UCAR
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import numpy as np
    import xarray as xr
    import pandas as pd
    import requests
except ImportError:
    print("Error: Required packages not installed.")
    print("Please run: pip install -r requirements.txt")
    sys.exit(1)


class GFSWaveDataFetcher:
    """Fetches and processes GFS Wave forecast data"""

    def __init__(self, output_dir='../data'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # OpenDAP endpoints for GFS Wave data (WAVEWATCH III)
        # Free government sources - tested and working
        self.opendap_urls = [
            # PacIOOS Hawaii ERDDAP - Working with WW3 global model
            'https://pae-paha.pacioos.hawaii.edu/erddap/griddap/ww3_global',
            # NOAA CoastWatch ERDDAP - Alternative
            'https://coastwatch.pfeg.noaa.gov/erddap/griddap/NWW3_Global_Best',
        ]

        # HTTPS access to GRIB files (modern NOAA approach)
        self.grib_https_url = 'https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod'

    def fetch_latest_forecast(self, max_timesteps=17):
        """
        Fetch the latest GFS wave forecast

        Args:
            max_timesteps: Number of forecast timesteps to retrieve (default: 17 = 48 hours at 3h intervals)

        Returns:
            dict: Processed wave data
        """
        print("Fetching latest GFS wave forecast...")

        # Try OpenDAP access first (most efficient)
        for url in self.opendap_urls:
            try:
                print(f"Attempting to fetch from: {url}")
                data = self._fetch_from_opendap(url, max_timesteps)
                if data:
                    return data
            except Exception as e:
                print(f"Failed to fetch from {url}: {e}")
                continue

        # If OpenDAP fails, try GRIB file download
        print("OpenDAP access failed, attempting GRIB file download...")
        try:
            return self._fetch_from_grib(max_timesteps)
        except Exception as e:
            print(f"GRIB fetch failed: {e}")

        print("All data fetch attempts failed. Using sample data.")
        return self._generate_sample_data()

    def _fetch_from_opendap(self, url, max_timesteps):
        """Fetch data via OpenDAP with lazy loading"""

        print(f"  Opening dataset with lazy loading...")

        # Open dataset with chunks for lazy loading (doesn't load all data)
        ds = xr.open_dataset(url, engine='netcdf4', chunks={'time': 10})

        # Get time dimension
        time_var = self._find_time_dimension(ds)
        total_times = len(ds[time_var])

        print(f"  Total timesteps available: {total_times}")
        print(f"  Selecting last {max_timesteps} timesteps...")

        # Slice to get only the last max_timesteps (lazy - doesn't load yet)
        ds = ds.isel({time_var: slice(-max_timesteps, None)})
        times = ds[time_var]

        print(f"  Selected {len(times)} timesteps")

        # Get wave parameters
        # PacIOOS ERDDAP variable names (primary source):
        # - Thgt: Significant wave height (meters)
        # - Tdir: Peak wave direction (degrees)
        # - Tper: Peak wave period (seconds)

        wave_height_vars = ['Thgt', 'HTSGW_surface', 'HTSGW', 'swh', 'VHM0', 'htsgwsfc', 'significant_wave_height']
        wave_dir_vars = ['Tdir', 'DIRPW_surface', 'DIRPW', 'mwd', 'VMDR', 'dirpwsfc', 'mean_wave_direction']
        wave_period_vars = ['Tper', 'PERPW_surface', 'PERPW', 'mwp', 'VTPK', 'perpwsfc', 'mean_wave_period']

        # Find available variables
        wave_height = self._find_variable(ds, wave_height_vars)
        wave_dir = self._find_variable(ds, wave_dir_vars)
        wave_period = self._find_variable(ds, wave_period_vars)

        if wave_height is None:
            raise ValueError("Could not find wave height variable in dataset")

        # Subsample spatial grid for performance (every 8th point = ~4 degrees for 0.5° data)
        print(f"  Subsampling spatial grid (every 8th point)...")
        lat_subsample = slice(None, None, 8)
        lon_subsample = slice(None, None, 8)

        # Extract data
        grid_data = []

        print(f"  Processing {len(times)} timesteps...")

        for t_idx in range(len(times)):
            # Get data for this timestep (this is when actual download happens)
            height_data = wave_height.isel({time_var: t_idx})[lat_subsample, lon_subsample].values

            if wave_dir is not None:
                dir_data = wave_dir.isel({time_var: t_idx})[lat_subsample, lon_subsample].values
            else:
                dir_data = None

            if wave_period is not None:
                period_data = wave_period.isel({time_var: t_idx})[lat_subsample, lon_subsample].values
            else:
                period_data = None

            # Get coordinates
            lat_name = self._find_variable(ds, ['lat', 'latitude', 'y'])
            lon_name = self._find_variable(ds, ['lon', 'longitude', 'x'])

            lats = ds[lat_name][lat_subsample].values
            lons = ds[lon_name][lon_subsample].values

            # Convert to list of points
            for i, lat in enumerate(lats):
                for j, lon in enumerate(lons):
                    height = float(height_data[i, j])

                    # Skip missing values
                    if np.isnan(height) or height < 0:
                        continue

                    point = {
                        'lat': float(lat),
                        'lon': float(lon),
                        'height': height,
                        'direction': float(dir_data[i, j]) if dir_data is not None else 0,
                        'period': float(period_data[i, j]) if period_data is not None else 8.0
                    }

                    grid_data.append(point)

            if (t_idx + 1) % 10 == 0:
                print(f"  Processed {t_idx + 1}/{len(times)} timesteps...")

        # Create timesteps
        timesteps = []
        time_values = times.values

        for t_idx in range(len(time_values)):
            try:
                # Try to convert to datetime
                time_val = time_values[t_idx]
                if np.issubdtype(type(time_val), np.datetime64):
                    dt = pd.Timestamp(time_val).to_pydatetime()
                else:
                    dt = datetime.utcfromtimestamp(float(time_val))
            except:
                # Fallback for different time formats
                dt = datetime.utcnow() + timedelta(hours=t_idx * 3)

            timesteps.append({
                'time': dt.isoformat(),
                'displayTime': dt.strftime('%b %d, %H:%M'),
                'index': t_idx
            })

        ds.close()

        print(f"  Successfully extracted {len(grid_data)} grid points")

        return {
            'timeSteps': timesteps,
            'gridData': grid_data,
            'metadata': {
                'source': 'WAVEWATCH III Global Wave Model (NOAA)',
                'resolution': '~4 degrees (subsampled from 0.5°)',
                'generated': datetime.utcnow().isoformat(),
                'url': url
            }
        }

    def _fetch_from_grib(self, max_timesteps):
        """Fetch data from GRIB files (alternative method)"""
        # This is more complex and requires cfgrib
        # For now, return None to fall back to sample data
        return None

    def _generate_sample_data(self):
        """Generate sample wave data for demonstration"""
        print("Generating sample wave data...")

        timeSteps = []
        now = datetime.utcnow()

        # Generate 80 timesteps (10 days at 3-hour intervals)
        for i in range(80):
            forecast_time = now + timedelta(hours=i * 3)
            timeSteps.append({
                'time': forecast_time.isoformat(),
                'displayTime': forecast_time.strftime('%b %d, %H:%M'),
                'index': i
            })

        # Generate grid data with better resolution
        grid_data = []
        for lat in range(-60, 61, 4):  # 4 degree spacing
            for lon in range(-180, 180, 4):
                # Simple ocean check (exclude major landmasses)
                if self._is_ocean(lat, lon):
                    height = abs(lat) / 30 + np.random.random() * 2
                    direction = (lon + 180 + np.random.random() * 60) % 360
                    period = 8 + np.random.random() * 4

                    grid_data.append({
                        'lat': float(lat),
                        'lon': float(lon),
                        'height': float(max(0.5, min(8, height))),
                        'direction': float(direction),
                        'period': float(period)
                    })

        return {
            'timeSteps': timeSteps,
            'gridData': grid_data,
            'metadata': {
                'source': 'Sample Data (Real NOAA data temporarily unavailable)',
                'resolution': '4 degrees',
                'generated': now.isoformat()
            }
        }

    def _is_ocean(self, lat, lon):
        """Simple ocean check (very simplified)"""
        # North America
        if 25 < lat < 50 and -125 < lon < -65:
            return False
        # Europe/Asia
        if 35 < lat < 55 and -10 < lon < 50:
            return False
        return True

    def _find_variable(self, ds, possible_names):
        """Find first available variable from list of possible names"""
        for name in possible_names:
            if name in ds.variables:
                return ds[name]
        return None

    def _find_time_dimension(self, ds):
        """Find the time dimension name"""
        time_names = ['time', 'time1', 'time2', 'valid_time', 'forecast_time']
        for name in time_names:
            if name in ds.dims or name in ds.coords:
                return name
        raise ValueError("Could not find time dimension in dataset")

    def save_to_json(self, data, filename='sample_data.json'):
        """Save data to JSON file"""
        output_path = self.output_dir / filename

        # Handle case where data is None
        if data is None:
            print("Error: No data to save")
            return None

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Data saved to: {output_path}")
        print(f"Grid points: {len(data['gridData'])}")
        print(f"Time steps: {len(data['timeSteps'])}")

        return output_path


def main():
    """Main function"""
    print("=" * 60)
    print("GFS Wave Data Fetcher")
    print("=" * 60)

    fetcher = GFSWaveDataFetcher()

    # Fetch latest forecast (80 timesteps = 10 days at 3-hour intervals)
    data = fetcher.fetch_latest_forecast(max_timesteps=80)

    # Save to JSON
    result = fetcher.save_to_json(data)

    if result and data:
        print("\nDone! Data is ready for visualization.")
        print(f"Source: {data['metadata']['source']}")
    else:
        print("\nWarning: Data fetch failed. No output file generated.")
        sys.exit(1)


if __name__ == '__main__':
    main()
