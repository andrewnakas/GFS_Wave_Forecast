/**
 * Velocity Field
 * Handles field generation and bilinear interpolation
 */
class VelocityField {
    constructor(waveData, map, options = {}) {
        this.waveData = waveData;
        this.map = map;
        this.options = options;

        this.grid = [];
        this.gridWidth = 0;
        this.gridHeight = 0;
        this.bounds = null;
        this.timeIndex = 0;

        this.build();
    }

    build() {
        const mapSize = this.map.getSize();
        this.bounds = this.map.getBounds();

        // Sample every 4 pixels for performance
        const spacing = 4;
        this.gridWidth = Math.ceil(mapSize.x / spacing);
        this.gridHeight = Math.ceil(mapSize.y / spacing);

        // Build grid as column-major (x, y)
        this.grid = [];

        for (let x = 0; x < this.gridWidth; x++) {
            const col = [];

            for (let y = 0; y < this.gridHeight; y++) {
                const px = x * spacing;
                const py = y * spacing;

                const latLng = this.map.containerPointToLatLng([px, py]);
                const wave = this.waveData.getWave(latLng.lat, latLng.lng, this.timeIndex);

                if (wave && !this.waveData.isLand(latLng.lat, latLng.lng)) {
                    // Convert wave to velocity vector
                    const uv = this.waveToVelocity(wave);
                    col[y] = [uv.u, uv.v, wave.height];
                } else {
                    col[y] = [0, 0, 0];
                }
            }

            this.grid[x] = col;
        }
    }

    waveToVelocity(wave) {
        // Convert wave direction (meteorological, coming from) to velocity vector
        // Direction 0 = from North, 90 = from East, etc.
        // We want the direction the wave is GOING TO (add 180)

        const directionTo = (wave.direction + 180) % 360;
        const radians = directionTo * Math.PI / 180;

        // Scale by velocityScale and wave height
        const scale = (this.options.velocityScale || 0.005) * 100;

        return {
            u: Math.sin(radians) * wave.height * scale,
            v: Math.cos(radians) * wave.height * scale
        };
    }

    // Bilinear interpolation at screen coordinates
    interpolate(x, y) {
        // Convert to grid coordinates
        const gx = x / 4;
        const gy = y / 4;

        // Grid cell indices
        const x0 = Math.floor(gx);
        const y0 = Math.floor(gy);
        const x1 = x0 + 1;
        const y1 = y0 + 1;

        // Check bounds
        if (x0 < 0 || x1 >= this.gridWidth || y0 < 0 || y1 >= this.gridHeight) {
            return null;
        }

        // Get four corners
        const q00 = this.grid[x0] && this.grid[x0][y0] ? this.grid[x0][y0] : [0, 0, 0];
        const q10 = this.grid[x1] && this.grid[x1][y0] ? this.grid[x1][y0] : [0, 0, 0];
        const q01 = this.grid[x0] && this.grid[x0][y1] ? this.grid[x0][y1] : [0, 0, 0];
        const q11 = this.grid[x1] && this.grid[x1][y1] ? this.grid[x1][y1] : [0, 0, 0];

        // Interpolation weights
        const fx = gx - x0;
        const fy = gy - y0;

        // Bilinear
        const w00 = (1 - fx) * (1 - fy);
        const w10 = fx * (1 - fy);
        const w01 = (1 - fx) * fy;
        const w11 = fx * fy;

        const u = q00[0] * w00 + q10[0] * w10 + q01[0] * w01 + q11[0] * w11;
        const v = q00[1] * w00 + q10[1] * w10 + q01[1] * w01 + q11[1] * w11;
        const m = q00[2] * w00 + q10[2] * w10 + q01[2] * w01 + q11[2] * w11;

        return { u, v, m };
    }

    // Check if position is in valid ocean area
    isValid(x, y) {
        const mapSize = this.map.getSize();

        if (x < 0 || x >= mapSize.x || y < 0 || y >= mapSize.y) {
            return false;
        }

        const latLng = this.map.containerPointToLatLng([x, y]);
        return !this.waveData.isLand(latLng.lat, latLng.lng);
    }

    // Update for new time
    setTime(timeIndex) {
        this.timeIndex = timeIndex;
        this.build();
    }

    // Rebuild on map move
    rebuild() {
        this.build();
    }
}
