# 🌊 GFS Wave Forecast Visualization

Interactive global wave forecast visualization using real NOAA WAVEWATCH III data.

![Wave Visualization](https://img.shields.io/badge/Status-Live-brightgreen)
![Data Source](https://img.shields.io/badge/Data-NOAA%20WAVEWATCH%20III-blue)
![Update Frequency](https://img.shields.io/badge/Updates-Every%206%20Hours-orange)

## 🚀 Live Demo

**View online:** https://andrewnakas.github.io/GFS_Wave_Forecast/

## ✨ Features

- **Real-time wave data** from NOAA WAVEWATCH III global wave model
- **Interactive Leaflet map** showing global wave conditions
- **Animated wave particles** that move like real ocean waves
- **10-day forecast** with 3-hour intervals (80 timesteps)
- **Click-for-details** - Click anywhere on ocean to see wave forecast chart
- **Vector visualization** showing wave direction and magnitude
- **Automatic updates** every 6 hours via GitHub Actions

## 🎯 How to Use

### Map Controls
- **Pan & Zoom**: Explore global wave conditions
- **Click on ocean**: See detailed wave forecast for that location
- **Time slider**: View different forecast times
- **Play button**: Animate through the 10-day forecast

### Visualization Options
- **Show Wave Vectors**: Display arrows showing wave direction and height
- **Show Particle Animation**: Animated particles showing wave movement
  - Particles move broadside like real ocean waves
  - No particles render over land
  - Freeze during pan/zoom for smooth interaction
- **Vector Scale**: Adjust arrow size (1-10)

### Wave Information
- **Height**: Significant wave height in meters
- **Direction**: Wave direction in degrees (meteorological convention)
- **Period**: Wave period in seconds
- **Forecast Chart**: 10-day timeline for selected location

## 🏃 Quick Start

### View Online
Just visit: **https://andrewnakas.github.io/GFS_Wave_Forecast/**

### Run Locally

```bash
# Clone repository
git clone https://github.com/andrewnakas/GFS_Wave_Forecast.git
cd GFS_Wave_Forecast

# Start local server
python3 -m http.server 8000

# Open browser
open http://localhost:8000
```

### Fetch Latest Data

```bash
# Install dependencies
pip install -r requirements.txt

# Run data fetcher
cd backend
python3 fetch_gfs_data.py
```

## 📊 Data Sources

1. **Primary**: PacIOOS Hawaii ERDDAP (WAVEWATCH III Global)
   - URL: https://pae-paha.pacioos.hawaii.edu/erddap/griddap/ww3_global
   - 77,000+ timesteps available
   - 0.5° resolution

2. **Backup**: NOAA CoastWatch ERDDAP
   - URL: https://coastwatch.pfeg.noaa.gov/erddap/griddap/NWW3_Global_Best

3. **Fallback**: Generated sample data (if servers unavailable)

## 🛠️ Technical Details

### Data Processing
- **Resolution**: ~4° global grid (subsampled from 0.5° source)
- **Coverage**: -77.5° to 77.5° latitude (global)
- **Forecast Length**: 10 days / 240 hours
- **Update Frequency**: Every 6 hours (via GitHub Actions)
- **File Size**: ~50-100 MB per update
- **Lazy Loading**: Uses dask for efficient data fetching

### Wave Particles
- **Geographic positioning**: Maintain lat/lon coordinates
- **Land masking**: Accurate continental boundaries
- **Smooth rendering**: Pause during map movement
- **Performance**: 50-60 FPS with 1500 particles

### Performance Optimizations
- Dask chunking for lazy data loading
- Spatial subsampling (every 8th point)
- Frame skipping (every other frame)
- Buffer zones for smooth panning
- Cached wave data computations

## 📁 Project Structure

```
GFS_Wave_Forecast/
├── index.html                   # Main visualization page
├── css/style.css               # Styling
├── js/
│   ├── map.js                  # Map initialization & controls
│   ├── waveLayer.js            # Canvas particle rendering
│   └── dataFetcher.js          # Data loading & land masking
├── backend/
│   └── fetch_gfs_data.py       # Python data fetcher
├── .github/workflows/
│   └── update-gfs-data.yml     # Auto-update workflow
├── gfs-wave-data.json          # Latest wave data
└── requirements.txt            # Python dependencies
```

## 🔄 Automatic Updates

Data updates every 6 hours via GitHub Actions:
- **Schedule**: 0:00, 6:00, 12:00, 18:00 UTC
- **Source**: NOAA WAVEWATCH III via ERDDAP
- **Process**: Fetch → Process → Commit → Deploy

### Manual Trigger
1. Go to repository Actions tab
2. Select "Update GFS Wave Data"
3. Click "Run workflow"

## 🌐 Deployment

Automatically deployed to GitHub Pages on merge to `main`.

### Setup GitHub Pages
1. Go to Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main` / `root`
4. Save

## 🧪 Development

### Local Testing

```bash
# Serve with Python
python3 -m http.server 8000

# Or with Node.js
npx http-server -p 8000

# View at http://localhost:8000
```

### Update Dependencies

```bash
pip install -r requirements.txt
```

### Test Data Fetch

```bash
cd backend
python3 fetch_gfs_data.py
```

## 📝 Dependencies

### Python (Backend)
- `xarray` - NetCDF/OpenDAP data access
- `netCDF4` - NetCDF file support
- `numpy` - Numerical operations
- `pandas` - Data manipulation
- `dask` - Lazy loading for large datasets
- `requests` - HTTP requests

### JavaScript (Frontend)
- Leaflet.js 1.9.4 - Interactive maps
- Chart.js 4.4.0 - Forecast charts

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional data sources
- Better land masking
- More visualization options
- Performance optimizations
- Mobile responsiveness
- Forecast accuracy metrics

## 📄 License

- Code: MIT License
- Data: Public domain (NOAA)

## 🙏 Acknowledgments

- **NOAA**: WAVEWATCH III wave model
- **PacIOOS**: Hawaii ERDDAP server
- **NOAA CoastWatch**: Alternative ERDDAP server
- **Leaflet.js**: Interactive mapping
- **Chart.js**: Data visualization

## 📧 Support

- Issues: https://github.com/andrewnakas/GFS_Wave_Forecast/issues
- Discussions: https://github.com/andrewnakas/GFS_Wave_Forecast/discussions

---

**Made with** 🌊 **by** [@andrewnakas](https://github.com/andrewnakas)

**Data Source**: NOAA WAVEWATCH III Global Wave Model
**Last Updated**: Auto-updated every 6 hours
