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
        # Free government sources
        self.opendap_urls = [
            # NOAA CoastWatch ERDDAP - Most reliable for recent data
            'https://coastwatch.pfeg.noaa.gov/erddap/griddap/NWW3_Global_Best',
            # NOAA NOMADS OpenDAP server
            'https://nomads.ncep.noaa.gov/dods/wave/gfswave',
            # UCAR THREDDS server
            'https://thredds.ucar.edu/thredds/dodsC/grib/NCEP/WW3/Global/Best',
            # NOAA AOML ERDDAP
            'https://erddap.aoml.noaa.gov/erddap/griddap/ww3_global',
        ]

        # Alternative: Direct GRIB file access from NOAA FTP
        self.grib_base_url = 'https://ftpprd.ncep.noaa.gov/data/nccf/com/gfs/prod'

        # AWS Open Data (backup)
        self.aws_base_url = 'https://noaa-gfs-bdp-pds.s3.amazonaws.com'

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
        """Fetch data via OpenDAP"""
        # Open dataset
        ds = xr.open_dataset(url, engine='netcdf4')

        # Get wave parameters
        # Common variable names in GFS Wave:
        # - HTSGW: Significant height of combined wind waves and swell
        # - DIRPW: Primary wave direction
        # - PERPW: Primary wave mean period

        wave_height_vars = ['HTSGW_surface', 'HTSGW', 'swh', 'VHM0']
        wave_dir_vars = ['DIRPW_surface', 'DIRPW', 'mwd', 'VMDR']
        wave_period_vars = ['PERPW_surface', 'PERPW', 'mwp', 'VTPK']

        # Find available variables
        wave_height = self._find_variable(ds, wave_height_vars)
        wave_dir = self._find_variable(ds, wave_dir_vars)
        wave_period = self._find_variable(ds, wave_period_vars)

        if not wave_height:
            raise ValueError("Could not find wave height variable in dataset")

        # Get time dimension
        time_var = self._find_time_dimension(ds)
        times = ds[time_var][:max_timesteps]

        # Subsample spatial grid for performance (every 4th point = ~1 degree)
        lat_subsample = slice(None, None, 4)
        lon_subsample = slice(None, None, 4)

        # Extract data
        grid_data = []

        for t_idx in range(min(max_timesteps, len(times))):
            # Get data for this timestep
            height_data = wave_height.isel({time_var: t_idx})[lat_subsample, lon_subsample]
            dir_data = wave_dir.isel({time_var: t_idx})[lat_subsample, lon_subsample] if wave_dir else None
            period_data = wave_period.isel({time_var: t_idx})[lat_subsample, lon_subsample] if wave_period else None

            # Get coordinates
            lat_name = self._find_variable(ds, ['lat', 'latitude', 'y'])
            lon_name = self._find_variable(ds, ['lon', 'longitude', 'x'])

            lats = ds[lat_name][lat_subsample]
            lons = ds[lon_name][lon_subsample]

            # Convert to list of points
            for i, lat in enumerate(lats.values):
                for j, lon in enumerate(lons.values):
                    height = float(height_data.values[i, j])

                    # Skip missing values
                    if np.isnan(height) or height < 0:
                        continue

                    point = {
                        'lat': float(lat),
                        'lon': float(lon),
                        'height': height,
                        'direction': float(dir_data.values[i, j]) if dir_data else 0,
                        'period': float(period_data.values[i, j]) if period_data else 8.0
                    }

                    grid_data.append(point)

        # Create timesteps
        timesteps = []
        for t_idx, time in enumerate(times.values):
            dt = datetime.utcfromtimestamp(time.astype('datetime64[s]').astype(int))
            timesteps.append({
                'time': dt.isoformat(),
                'displayTime': dt.strftime('%b %d, %H:%M'),
                'index': t_idx
            })

        ds.close()

        return {
            'timeSteps': timesteps,
            'gridData': grid_data,
            'metadata': {
                'source': 'GFS Wave (WAVEWATCH III)',
                'resolution': '0.25 degrees (subsampled to ~1 degree)',
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

        for i in range(17):
            forecast_time = now + timedelta(hours=i * 3)
            timeSteps.append({
                'time': forecast_time.isoformat(),
                'displayTime': forecast_time.strftime('%b %d, %H:%M'),
                'index': i
            })

        # Generate grid data
        grid_data = []
        for lat in range(-60, 61, 2):
            for lon in range(-180, 180, 2):
                # Simple ocean check (exclude major landmasses)
                if self._is_ocean(lat, lon):
                    height = abs(lat) / 30 + np.random.random() * 2
                    direction = (lon + 180 + np.random.random() * 60) % 360
                    period = 8 + np.random.random() * 4

                    grid_data.append({
                        'lat': lat,
                        'lon': lon,
                        'height': max(0.5, min(8, height)),
                        'direction': direction,
                        'period': period
                    })

        return {
            'timeSteps': timeSteps,
            'gridData': grid_data,
            'metadata': {
                'source': 'Sample Data (for demonstration)',
                'resolution': '2 degrees',
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
    fetcher.save_to_json(data)

    print("\nDone! Data is ready for visualization.")
    print(f"Source: {data['metadata']['source']}")


if __name__ == '__main__':
    main()
