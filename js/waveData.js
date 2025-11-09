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

        console.log(`Wave data initialized: ${this.waveGrid.size} ocean grid points, ${this.timeSteps.length} time steps`);

        // Test sample
        const testWave = this.getWave(30, -150, 0);
        if (testWave) {
            console.log(`Sample wave at 30°N, 150°W: height=${testWave.height.toFixed(2)}m, direction=${testWave.direction.toFixed(0)}°`);
        }
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
        // Create key directly from lat/lon
        const latIdx = Math.round(lat / this.resolution);
        const lonIdx = Math.round(lon / this.resolution);
        const key = `${latIdx},${lonIdx}`;

        const wave = this.waveGrid.get(key);

        if (!wave) return null;

        // Add time variation
        const timeFactor = Math.sin(timeIndex * 0.3) * 0.2;

        return {
            lat: wave.lat,
            lon: wave.lon,
            height: wave.height * (1 + timeFactor),
            direction: (wave.direction + timeIndex * 5) % 360,
            period: wave.period
        };
    }

    isLand(lat, lon) {
        // Normalize
        while (lon > 180) lon -= 360;
        while (lon < -180) lon += 360;

        // Much more conservative land mask - only core continental areas
        // This leaves most ocean areas free for wave particles

        // Antarctica (far south only)
        if (lat < -70) return true;

        // Arctic Ocean ice cap (far north only)
        if (lat > 85) return true;

        // North America - more conservative boundaries
        // Exclude Gulf of Alaska, coastal areas
        if (lat > 25 && lat < 65 && lon > -125 && lon < -65) return true;

        // Central America (narrow band)
        if (lat > 8 && lat < 25 && lon > -100 && lon < -80) return true;

        // South America - core only
        if (lat > -40 && lat < 10 && lon > -75 && lon < -40) return true;

        // Europe (conservative)
        if (lat > 40 && lat < 70 && lon > -10 && lon < 40) return true;

        // Africa (core only)
        if (lat > -30 && lat < 35 && lon > 0 && lon < 45) return true;

        // Asia - broken into regions
        // Middle East / Central Asia
        if (lat > 15 && lat < 50 && lon > 40 && lon < 80) return true;

        // East Asia (China, Japan region)
        if (lat > 20 && lat < 50 && lon > 100 && lon < 135) return true;

        // Southeast Asia (narrow)
        if (lat > 0 && lat < 25 && lon > 95 && lon < 110) return true;

        // Australia (core only)
        if (lat > -35 && lat < -15 && lon > 120 && lon < 145) return true;

        return false;
    }

    getTimeSteps() {
        return this.timeSteps;
    }
}
