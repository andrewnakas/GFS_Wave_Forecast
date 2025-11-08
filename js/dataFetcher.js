/**
 * GFS Wave Data Fetcher
 * Handles fetching and processing wave forecast data
 */

class GFSDataFetcher {
    constructor() {
        this.baseURL = 'backend/sample_data.json'; // For demo, using local data
        // In production, this would point to: 'https://thredds.ucar.edu/thredds/dodsC/grib/NCEP/WW3/Global/Best'
        this.data = null;
        this.currentTimeIndex = 0;
        this.timeSteps = [];
    }

    /**
     * Initialize and fetch wave data
     */
    async initialize() {
        try {
            await this.fetchData();
            return this.data;
        } catch (error) {
            console.error('Error initializing data fetcher:', error);
            // If backend data fails, generate sample data
            return this.generateSampleData();
        }
    }

    /**
     * Fetch data from backend
     */
    async fetchData() {
        try {
            const response = await fetch(this.baseURL);
            if (!response.ok) {
                throw new Error('Failed to fetch data');
            }
            this.data = await response.json();
            this.timeSteps = this.data.timeSteps || [];
            return this.data;
        } catch (error) {
            console.warn('Could not fetch backend data, generating sample data:', error);
            return this.generateSampleData();
        }
    }

    /**
     * Generate sample wave data for demonstration
     * This simulates GFS wave forecast data
     */
    generateSampleData() {
        const timeSteps = [];
        const now = new Date();

        // Generate 10 days of forecast at 3-hour intervals (80 timesteps)
        for (let i = 0; i < 80; i++) {
            const forecastTime = new Date(now.getTime() + i * 3 * 60 * 60 * 1000);
            timeSteps.push({
                time: forecastTime.toISOString(),
                displayTime: forecastTime.toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                }),
                index: i
            });
        }

        this.timeSteps = timeSteps;

        // Generate grid data
        const gridData = this.generateGridData();

        this.data = {
            timeSteps: timeSteps,
            gridData: gridData,
            metadata: {
                source: 'GFS Wave (WAVEWATCH III) - Ultra Performance Mode',
                resolution: '4 degrees (maximum performance)',
                generated: now.toISOString()
            }
        };

        return this.data;
    }

    /**
     * Generate wave grid data
     */
    generateGridData() {
        const grid = [];
        const latStep = 4.0; // 4 degree resolution for maximum performance
        const lonStep = 4.0;

        // Generate data for global ocean (simplified)
        for (let lat = -60; lat <= 60; lat += latStep) {
            for (let lon = -180; lon < 180; lon += lonStep) {
                // Skip land masses (simplified)
                if (this.isOcean(lat, lon)) {
                    grid.push({
                        lat: lat,
                        lon: lon,
                        // Generate realistic-looking wave data
                        height: this.generateWaveHeight(lat, lon),
                        direction: this.generateWaveDirection(lat, lon),
                        period: this.generateWavePeriod(lat, lon)
                    });
                }
            }
        }

        return grid;
    }

    /**
     * Check if location is on land (improved land masking)
     */
    isLand(lat, lon) {
        // North America
        if (lat > 15 && lat < 72 && lon > -170 && lon < -50) return true;

        // South America
        if (lat > -55 && lat < 13 && lon > -82 && lon < -35) return true;

        // Europe
        if (lat > 35 && lat < 71 && lon > -10 && lon < 40) return true;

        // Africa
        if (lat > -35 && lat < 37 && lon > -18 && lon < 52) return true;

        // Asia (main landmass)
        if (lat > 5 && lat < 75 && lon > 40 && lon < 150) return true;

        // Australia
        if (lat > -45 && lat < -10 && lon > 110 && lon < 155) return true;

        // Greenland
        if (lat > 59 && lat < 84 && lon > -75 && lon < -10) return true;

        // Antarctica
        if (lat < -60) return true;

        // Japan
        if (lat > 30 && lat < 46 && lon > 128 && lon < 146) return true;

        // New Zealand
        if (lat > -48 && lat < -34 && lon > 165 && lon < 180) return true;

        // Southeast Asia islands (simplified)
        if (lat > -10 && lat < 20 && lon > 95 && lon < 125) return true;

        // Central America
        if (lat > 7 && lat < 22 && lon > -92 && lon < -77) return true;

        // Caribbean islands (simplified)
        if (lat > 10 && lat < 27 && lon > -85 && lon < -60) return true;

        // Mediterranean (simplified)
        if (lat > 30 && lat < 46 && lon > 0 && lon < 42) return true;

        return false;
    }

    /**
     * Check if location is ocean
     */
    isOcean(lat, lon) {
        return !this.isLand(lat, lon);
    }

    /**
     * Generate realistic wave height based on location
     */
    generateWaveHeight(lat, lon) {
        const baseHeight = Math.abs(lat) / 30; // Higher waves at higher latitudes
        const noise = Math.sin(lon * 0.1) * Math.cos(lat * 0.1) * 2;
        const random = Math.random() * 0.5;
        return Math.max(0.5, Math.min(8, baseHeight + noise + random));
    }

    /**
     * Generate wave direction (degrees from north)
     */
    generateWaveDirection(lat, lon) {
        // Simulate prevailing wave patterns
        const baseDirection = (lon + 180) % 360;
        const latInfluence = lat > 0 ? 45 : -45;
        const noise = (Math.random() - 0.5) * 60;
        return (baseDirection + latInfluence + noise + 360) % 360;
    }

    /**
     * Generate wave period (seconds)
     */
    generateWavePeriod(lat, lon) {
        const basePeriod = 8;
        const variation = Math.sin(lon * 0.05) * 4;
        return Math.max(4, Math.min(16, basePeriod + variation));
    }

    /**
     * Get data for specific time index
     */
    getDataForTime(timeIndex) {
        if (!this.data || !this.data.gridData) {
            return null;
        }

        // In a real implementation, this would fetch time-specific data
        // For now, we'll add time-based variation to the base data
        return this.data.gridData.map(point => ({
            ...point,
            height: point.height * (1 + Math.sin(timeIndex * 0.3) * 0.2),
            direction: (point.direction + timeIndex * 5) % 360
        }));
    }

    /**
     * Get wave data at specific location
     */
    getWaveAtLocation(lat, lon, timeIndex = this.currentTimeIndex) {
        const data = this.getDataForTime(timeIndex);
        if (!data) return null;

        // Find nearest grid point
        let nearest = null;
        let minDist = Infinity;

        for (const point of data) {
            const dist = Math.sqrt(
                Math.pow(point.lat - lat, 2) +
                Math.pow(point.lon - lon, 2)
            );
            if (dist < minDist) {
                minDist = dist;
                nearest = point;
            }
        }

        return nearest;
    }

    /**
     * Convert wave direction to vector components (u, v)
     */
    directionToVector(direction, magnitude) {
        // Direction is "coming from" in meteorological convention
        // Convert to radians and get components
        const radians = (direction + 180) % 360 * Math.PI / 180;
        return {
            u: magnitude * Math.sin(radians),
            v: magnitude * Math.cos(radians)
        };
    }

    /**
     * Get time steps
     */
    getTimeSteps() {
        return this.timeSteps;
    }

    /**
     * Set current time index
     */
    setTimeIndex(index) {
        this.currentTimeIndex = Math.max(0, Math.min(index, this.timeSteps.length - 1));
    }
}
