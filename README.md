# GFS Wave Forecast Visualization

A global wave forecast visualization using real GFS (Global Forecast System) wave data, displayed with the leaflet-velocity particle animation library.

## Features

- **Real GFS Wave Data**: Automatically fetches latest wave forecasts from NOAA every 6 hours
- **Beautiful Visualization**: Smooth particle animation using leaflet-velocity
- **Global Coverage**: 0.25° resolution global wave model data
- **Auto-updating**: GitHub Actions workflow updates data automatically
- **Fallback Data**: Synthetic wave data when GFS data unavailable

## Live Demo

The visualization is automatically deployed to GitHub Pages from the main branch.

## How It Works

### Data Flow

1. **GitHub Actions** runs every 6 hours (at 15 minutes past 00, 06, 12, 18 UTC)
2. **Python Script** (`fetch_gfs_data.py`) fetches latest GFS wave GRIB2 data from NOAA
3. **Data Conversion** converts wave direction and height to U/V velocity components
4. **JSON Export** saves data in leaflet-velocity format as `gfs-wave-data.json`
5. **Auto-commit** commits the updated data file to the repository
6. **GitHub Pages** serves the updated visualization

### Frontend

- **leaflet.js**: Interactive map library
- **leaflet-velocity**: Particle animation layer
- **wave-data.js**: Loads GFS data or fallback synthetic data
- **index.html**: Simple, clean interface

## Local Development

### Prerequisites

For fetching real GFS data:
```bash
pip install xarray cfgrib requests numpy eccodes
```

### Manual Data Fetch

```bash
python fetch_gfs_data.py
```

This will:
1. Determine the latest GFS cycle
2. Download the GRIB2 file from NOAA
3. Parse wave height, direction, and period
4. Convert to U/V velocity components
5. Save as `gfs-wave-data.json`

### Serve Locally

```bash
python -m http.server 8000
```

Then open http://localhost:8000 in your browser.

## GFS Data Parameters

The script fetches these wave parameters:

- **HTSGW**: Significant Height of Combined Wind Waves and Swell
- **DIRPW**: Primary Wave Direction (degrees)
- **PERPW**: Primary Wave Mean Period (seconds)

These are converted to eastward (U) and northward (V) velocity components for particle animation.

## Data Format

The leaflet-velocity library expects data in this format:

```javascript
[
  {
    "header": {
      "dx": 0.25,          // longitude spacing
      "dy": 0.25,          // latitude spacing
      "nx": 1440,          // number of longitude points
      "ny": 721,           // number of latitude points
      "la1": 90,           // north latitude
      "la2": -90,          // south latitude
      "lo1": 0,            // west longitude
      "lo2": 359.75        // east longitude
    },
    "data": [...]          // U component (eastward)
  },
  {
    "header": {...},
    "data": [...]          // V component (northward)
  }
]
```

## GitHub Actions Workflow

The `.github/workflows/fetch-gfs-data.yml` workflow:

- **Schedule**: Runs every 6 hours
- **Manual Trigger**: Can be triggered manually from Actions tab
- **Auto-commit**: Automatically commits updated data
- **Dependencies**: Installs Python packages needed for GRIB2 parsing

## Fallback Behavior

If GFS data cannot be fetched (network issues, NOAA downtime, etc.), the app falls back to synthetic wave data that simulates realistic global wave patterns based on:

- Southern Ocean westerlies
- Mid-latitude storm tracks
- Trade wind zones
- Equatorial patterns

## Customization

### Adjust Particle Appearance

Edit `index.html` to change velocity layer options:

```javascript
const velocityLayer = L.velocityLayer({
    maxVelocity: 10,      // color scale max
    velocityScale: 0.01,  // particle speed
    colorScale: [...]     // particle colors
});
```

### Change Update Frequency

Edit `.github/workflows/fetch-gfs-data.yml`:

```yaml
schedule:
  - cron: '15 */6 * * *'  # Every 6 hours at :15
```

### Use Different Forecast Hours

Edit `fetch_gfs_data.py`:

```python
wave_data = fetch_gfs_wave_data(cycle_time, forecast_hour=6)  # 6-hour forecast
```

## Data Sources

- **NOAA NOMADS**: https://nomads.ncep.noaa.gov/
- **AWS S3 Mirror**: https://noaa-gfs-bdp-pds.s3.amazonaws.com/

## Technical Notes

### GRIB2 Parsing

Uses `xarray` with `cfgrib` backend to parse GRIB2 files. This requires the ECCODES library to be installed.

### Wave Direction Convention

GFS uses meteorological convention (direction FROM which waves come). The script converts this to mathematical angles for U/V component calculation.

### Grid Ordering

Data is ordered from north to south, west to east, matching the leaflet-velocity expected format.

## Troubleshooting

### GFS Data Not Loading

1. Check GitHub Actions logs for errors
2. Verify NOAA servers are accessible
3. Check if GFS cycle is available (data published ~4 hours after cycle time)
4. App will fall back to synthetic data automatically

### Particles Not Showing

1. Open browser console and check for errors
2. Verify `wave-data.js` loaded successfully
3. Check that `waveDataReady` event fired
4. Ensure leaflet-velocity CDN is accessible

### GitHub Actions Failing

1. Check that Python dependencies install correctly
2. Verify ECCODES system library is available
3. Check NOAA server availability
4. Review workflow logs for specific errors

## Future Enhancements

- [ ] Add time slider for forecast hours (0, 3, 6, ..., 120)
- [ ] Show wave height legend
- [ ] Add click-to-show local wave conditions
- [ ] Implement wave period visualization
- [ ] Add swell direction overlay
- [ ] Cache multiple forecast hours
- [ ] Add animation play/pause controls

## License

MIT License - see LICENSE file

## Credits

- **GFS Wave Model**: NOAA/NCEP
- **leaflet.js**: Vladimir Agafonkin
- **leaflet-velocity**: Danwild
- **Map Tiles**: CartoDB

## Support

For issues or questions, please open an issue on GitHub.
