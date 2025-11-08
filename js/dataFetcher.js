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

        // Generate 48 hours of forecast at 3-hour intervals
        for (let i = 0; i < 17; i++) {
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
                source: 'GFS Wave (WAVEWATCH III)',
                resolution: '0.25 degrees',
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
        const latStep = 1.0; // 1 degree resolution for demo
        const lonStep = 1.0;

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
     * Simple ocean check (very simplified)
     */
    isOcean(lat, lon) {
        // Simplified: exclude some obvious land masses
        // In reality, this would use proper land/sea mask

        // North America
        if (lat > 25 && lat < 50 && lon > -125 && lon < -65) return false;
        // Europe/Asia landmass (simplified)
        if (lat > 35 && lat < 55 && lon > -10 && lon < 50) return false;

        return true;
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
