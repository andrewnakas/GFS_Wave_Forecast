/**
 * Global Wave Data Generator
 * Generates realistic wave patterns for visualization
 */
class WaveDataGenerator {
    constructor() {
        this.resolution = 2.5; // degrees
        this.timeSteps = [];
        this.waveGrid = null;

        this.init();
    }

    init() {
        // Generate time steps (80 forecasts, 3-hour intervals)
        const now = Date.now();
        for (let i = 0; i < 80; i++) {
            const time = new Date(now + i * 3 * 3600 * 1000);
            this.timeSteps.push({
                index: i,
                time: time,
                display: time.toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                })
            });
        }

        // Generate base wave field
        this.generateWaveGrid();
    }

    generateWaveGrid() {
        this.waveGrid = new Map();

        // Generate global wave patterns
        for (let lat = -85; lat <= 85; lat += this.resolution) {
            for (let lon = -180; lon < 180; lon += this.resolution) {

                // Skip land (simplified)
                if (this.isLand(lat, lon)) continue;

                const key = this.gridKey(lat, lon);

                // Generate realistic wave patterns based on latitude
                const absLat = Math.abs(lat);

                // Higher waves at higher latitudes (storm tracks)
                const baseHeight = (absLat / 90) * 6;

                // Add some variability based on longitude
                const lonVariation = Math.sin(lon * Math.PI / 180) * 2;

                // Add noise
                const noise = (Math.random() - 0.5) * 1.5;

                const height = Math.max(0.2, baseHeight + lonVariation + noise);

                // Direction generally follows prevailing winds
                // Westerlies in mid-latitudes, trades in tropics
                let direction;
                if (absLat > 30) {
                    // Westerlies (coming from west, going east)
                    direction = 270 + (Math.random() - 0.5) * 60;
                } else {
                    // Trade winds (coming from east, going west)
                    direction = 90 + (Math.random() - 0.5) * 60;
                }

                // Add rotational component in northern/southern hemispheres
                if (lat > 0) {
                    direction += 15;
                } else {
                    direction -= 15;
                }

                direction = (direction + 360) % 360;

                this.waveGrid.set(key, {
                    lat,
                    lon,
                    height,
                    direction,
                    period: 6 + height * 1.5 // Longer period for bigger waves
                });
            }
        }
    }

    gridKey(lat, lon) {
        return `${Math.round(lat / this.resolution)},${Math.round(lon / this.resolution)}`;
    }

    getWave(lat, lon, timeIndex = 0) {
        // Snap to grid
        const snapLat = Math.round(lat / this.resolution) * this.resolution;
        const snapLon = Math.round(lon / this.resolution) * this.resolution;

        const key = this.gridKey(snapLat, snapLon);
        const wave = this.waveGrid.get(key);

        if (!wave) return null;

        // Add time variation
        const timeFactor = Math.sin(timeIndex * 0.3) * 0.2;

        return {
            ...wave,
            height: wave.height * (1 + timeFactor),
            direction: (wave.direction + timeIndex * 5) % 360
        };
    }

    isLand(lat, lon) {
        // Normalize
        while (lon > 180) lon -= 360;
        while (lon < -180) lon += 360;

        // Simplified land mask - major continents

        // Antarctica
        if (lat < -60) return true;

        // Arctic
        if (lat > 80) return true;

        // North America
        if (lat > 15 && lat < 75 && lon > -170 && lon < -50) return true;

        // South America
        if (lat > -55 && lat < 15 && lon > -85 && lon < -30) return true;

        // Europe/Africa
        if (lat > -35 && lat < 75 && lon > -15 && lon < 50) return true;

        // Asia
        if (lat > 5 && lat < 75 && lon > 50 && lon < 145) return true;

        // Australia
        if (lat > -45 && lat < -10 && lon > 110 && lon < 155) return true;

        return false;
    }

    getTimeSteps() {
        return this.timeSteps;
    }
}
