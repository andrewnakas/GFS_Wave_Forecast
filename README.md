# GFS Wave Forecast Visualization

An interactive web-based visualization of Global Forecast System (GFS) wave data with animated wave velocity vectors on a Leaflet map.

![GFS Wave Forecast](https://img.shields.io/badge/Data-NOAA%20GFS%20Wave-blue)
![License](https://img.shields.io/badge/License-MIT-green)

**[🌊 View Live Demo](https://andrewnakas.github.io/GFS_Wave_Forecast/)** ← Try it now!

## Features

- **Real-time GFS wave forecast visualization** - Access the latest wave forecasts from NOAA
- **Animated wave vectors** - See wave direction and magnitude with dynamic arrows
- **Particle animation** - Watch particles flow with wave currents
- **Interactive map** - Zoom, pan, and click anywhere for detailed wave information
- **Time controls** - Navigate through 48 hours of forecast with play/pause controls
- **Customizable display** - Adjust vector scale and toggle layers
- **Color-coded wave heights** - Instantly identify wave intensity

## Quick Start

### Option 1: View Online (Easiest!)

**Just visit the live demo:** [https://andrewnakas.github.io/GFS_Wave_Forecast/](https://andrewnakas.github.io/GFS_Wave_Forecast/)

The app is automatically deployed via GitHub Actions and works immediately in your browser with sample wave data.

### Option 2: Run Locally

```bash
# Clone the repository
git clone https://github.com/andrewnakas/GFS_Wave_Forecast.git
cd GFS_Wave_Forecast

# Start the server
python backend/simple_server.py

# Open your browser to http://localhost:8000
```

That's it! The application will load with sample wave data and start animating.

## Data Source

Wave data is sourced from NOAA's **GFS Wave model** (WAVEWATCH III) via OpenDAP/THREDDS services:
- Primary: UCAR THREDDS Server
- Alternative: NOAA NOMADS Server
- Format: NetCDF/GRIB2
- Resolution: 0.25° (subsampled to ~1° for performance)
- Forecast: 16 days, 3-hour intervals

## Project Structure

```
├── index.html          # Main HTML page
├── css/
│   └── style.css       # Styling
├── js/
│   ├── map.js          # Leaflet map initialization
│   ├── waveLayer.js    # Wave velocity animation layer
│   └── dataFetcher.js  # GFS data fetching and processing
├── backend/
│   ├── fetch_gfs_data.py  # Python script to fetch and process GRIB data
│   └── requirements.txt   # Python dependencies
└── data/
    └── .gitkeep        # Data directory for cached wave data
```

## Advanced Setup - Fetching Real GFS Data

To fetch real-time GFS wave forecast data from NOAA:

### Prerequisites

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt
```

### Fetch Latest Data

```bash
# Run the data fetcher
python fetch_gfs_data.py
```

This will:
1. Connect to NOAA's THREDDS/OpenDAP servers
2. Download the latest GFS wave forecast
3. Process and save the data to `data/sample_data.json`
4. The web app will automatically use this data

Note: The data fetcher will fall back to generating sample data if:
- Network connectivity issues
- NOAA servers are unavailable
- Required Python packages are missing

## Usage Guide

### Basic Controls

1. **Map Navigation**
   - Click and drag to pan
   - Scroll to zoom in/out
   - Click anywhere on the ocean to see wave details

2. **Time Controls**
   - Use the slider to jump to any forecast time
   - Click **Play** to animate through the forecast
   - Click **Reset** to return to the start

3. **Display Options**
   - Toggle **Wave Vectors** to show/hide directional arrows
   - Toggle **Particle Animation** to show/hide particle flow
   - Adjust **Vector Scale** to change arrow size

4. **Wave Information**
   - Click any ocean point to see:
     - Wave height (meters)
     - Wave direction (degrees and compass direction)
     - Wave period (seconds)
     - Geographic coordinates

### Understanding the Visualization

- **Arrow Direction**: Shows where waves are traveling TO
- **Arrow Length**: Proportional to wave height
- **Arrow Color**:
  - Blue = Small waves (0-2m)
  - Cyan = Moderate waves (2-4m)
  - Orange = Large waves (4-6m)
  - Red = Very large waves (6m+)
- **Particles**: Flow with wave currents, showing overall wave patterns

## Technologies Used

### Frontend
- **Leaflet.js** (v1.9.4) - Interactive web mapping
- **Canvas API** - Custom vector and particle rendering
- **Vanilla JavaScript** - No framework dependencies

### Backend
- **Python 3.8+** - Data processing
- **xarray** - Multi-dimensional array handling
- **NetCDF4** - NetCDF file access
- **cfgrib** - GRIB2 file decoding
- **NumPy** - Numerical computations

### Data Sources
- **NOAA GFS Wave** - Global wave forecasts
- **WAVEWATCH III** - Wave model
- **UCAR THREDDS** - OpenDAP data access
- **NOAA NOMADS** - Alternative data source

## Troubleshooting

### The map doesn't load
- Make sure you're running a web server (don't open `index.html` directly)
- Check browser console for errors
- Try `python backend/simple_server.py`

### No wave vectors showing
- Check that "Show Wave Vectors" is enabled in the control panel
- Try adjusting the vector scale slider
- Zoom in closer to the map

### Python data fetcher fails
- The app will work with sample data if real data fetch fails
- Check your internet connection
- Verify Python packages are installed: `pip install -r backend/requirements.txt`
- NOAA servers may be temporarily unavailable - try again later

### Performance issues
- The application uses ~3000 animated particles which may be intensive
- Try disabling particle animation in the control panel
- Close other browser tabs
- Zoom to a specific region instead of viewing the whole globe

## Deployment

### GitHub Pages (Automatic)

This project is configured for automatic deployment to GitHub Pages using GitHub Actions.

**To enable for your fork:**

1. Go to your repository Settings → Pages
2. Under "Build and deployment":
   - Source: Select "GitHub Actions"
3. Push to `main` or `master` branch
4. The workflow will automatically:
   - Attempt to fetch latest GFS data from NOAA
   - Fall back to sample data if fetch fails
   - Deploy to GitHub Pages
5. Your site will be live at: `https://[your-username].github.io/GFS_Wave_Forecast/`

**Manual deployment trigger:**
- Go to Actions tab → "Deploy to GitHub Pages" → "Run workflow"

### Other Hosting Options

The application is purely static HTML/CSS/JavaScript and can be deployed to:
- **Netlify**: Drag and drop the project folder
- **Vercel**: Connect your GitHub repo
- **GitHub Codespaces**: Works out of the box
- **Any static host**: Just upload the files

## Future Enhancements

- [ ] Add backend API for automated data updates
- [ ] Implement WebSocket for real-time data streaming
- [ ] Add weather overlay (wind, pressure, temperature)
- [ ] Support for additional wave models (ECMWF, regional models)
- [ ] Historical wave data playback
- [ ] Export capabilities (images, data)
- [ ] Mobile-optimized interface
- [ ] Integration with weather forecast data
- [x] GitHub Actions deployment
- [x] GitHub Pages hosting

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- **NOAA** - For providing free access to GFS wave forecast data
- **UCAR** - For THREDDS data server infrastructure
- **Leaflet.js** - For excellent open-source mapping library

## License

See LICENSE file for details.

## Contact

For questions or issues, please open an issue on GitHub.
