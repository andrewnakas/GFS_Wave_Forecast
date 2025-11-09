/**
 * Wave Velocity Layer - Faithful implementation of leaflet-velocity for wave data
 * Based on https://github.com/onaci/leaflet-velocity
 */

class WaveVelocityLayer {
    constructor(map, dataFetcher, options = {}) {
        this.map = map;
        this.dataFetcher = dataFetcher;

        this.options = Object.assign({
            displayValues: true,
            maxVelocity: 10,
            velocityScale: 0.005,
            colorScale: [
                "rgb(36,104,180)",
                "rgb(60,157,194)",
                "rgb(128,205,193)",
                "rgb(151,218,168)",
                "rgb(198,231,181)",
                "rgb(238,247,217)",
                "rgb(255,238,159)",
                "rgb(252,217,125)",
                "rgb(255,182,100)",
                "rgb(252,150,75)",
                "rgb(250,112,52)",
                "rgb(245,64,32)",
                "rgb(237,45,28)",
                "rgb(220,24,32)",
                "rgb(180,0,35)"
            ],
            frameRate: 15,
            particleMultiplier: 1/300,
            particleAge: 90,
            lineWidth: 2,
            opacity: 0.97
        }, options);

        this.canvas = null;
        this.ctx = null;
        this.field = null;
        this.particles = [];
        this.animationFrame = null;
        this.then = Date.now();

        this.initCanvas();
    }

    initCanvas() {
        const CanvasLayer = L.Layer.extend({
            onAdd: (map) => {
                this.canvas = L.DomUtil.create('canvas', 'leaflet-zoom-hide');
                this.ctx = this.canvas.getContext('2d');

                const size = map.getSize();
                this.canvas.width = size.x;
                this.canvas.height = size.y;

                this.canvas.style.position = 'absolute';
                this.canvas.style.top = '0';
                this.canvas.style.left = '0';
                this.canvas.style.pointerEvents = 'none';

                map.getPanes().overlayPane.appendChild(this.canvas);

                map.on('moveend', () => this.reset());
                map.on('resize', () => this.resize());

                this.buildField();
            },

            onRemove: (map) => {
                this.stop();
                if (this.canvas && this.canvas.parentNode) {
                    this.canvas.parentNode.removeChild(this.canvas);
                }
                map.off('moveend');
                map.off('resize');
            }
        });

        this.layer = new CanvasLayer();
        this.layer.addTo(this.map);
    }

    buildField() {
        const bounds = this.map.getBounds();
        const size = this.map.getSize();
        const width = size.x;
        const height = size.y;

        // Get wave data for current time
        const waveData = this.dataFetcher.getDataForTime(this.dataFetcher.currentTimeIndex);
        if (!waveData || waveData.length === 0) {
            console.warn('No wave data available');
            return;
        }

        // Build velocity field grid
        const columns = [];
        const pointsPerColumn = Math.ceil(height / 4);
        const columnsCount = Math.ceil(width / 4);

        for (let x = 0; x < columnsCount; x++) {
            const column = [];
            for (let y = 0; y < pointsPerColumn; y++) {
                const px = x * 4;
                const py = y * 4;

                if (px >= width || py >= height) continue;

                const latLng = this.map.containerPointToLatLng([px, py]);
                const wave = this.getWaveAtPoint(latLng.lat, latLng.lng, waveData);

                if (wave && !this.dataFetcher.isLand(latLng.lat, latLng.lng)) {
                    // Convert wave direction and height to velocity components
                    const vector = this.waveToVector(wave.direction, wave.height);
                    column[y] = [vector.u, vector.v, wave.height];
                } else {
                    column[y] = [0, 0, 0];
                }
            }
            columns[x] = column;
        }

        // Create field object with interpolation
        this.field = {
            bounds: bounds,
            width: width,
            height: height,
            columns: columns,

            // Get value at specific pixel coordinates
            valueAt: (x, y) => {
                if (x < 0 || x >= width || y < 0 || y >= height) {
                    return null;
                }

                const column = Math.floor(x / 4);
                const row = Math.floor(y / 4);

                if (!columns[column] || !columns[column][row]) {
                    return [0, 0, 0];
                }

                return columns[column][row];
            },

            // Bilinear interpolation
            interpolate: (x, y) => {
                const x0 = Math.floor(x / 4);
                const y0 = Math.floor(y / 4);
                const x1 = x0 + 1;
                const y1 = y0 + 1;

                if (!columns[x0] || !columns[x1]) {
                    return [0, 0, 0];
                }

                const g00 = columns[x0][y0] || [0, 0, 0];
                const g10 = columns[x1][y0] || [0, 0, 0];
                const g01 = columns[x0][y1] || [0, 0, 0];
                const g11 = columns[x1][y1] || [0, 0, 0];

                // Interpolation weights
                const fx = (x / 4) - x0;
                const fy = (y / 4) - y0;

                return this.bilinearInterpolate(fx, fy, g00, g10, g01, g11);
            },

            // Check if point is valid (not on land, within bounds)
            isDefined: (x, y) => {
                if (x < 0 || x >= width || y < 0 || y >= height) {
                    return false;
                }

                const latLng = this.map.containerPointToLatLng([x, y]);
                return !this.dataFetcher.isLand(latLng.lat, latLng.lng);
            },

            // Random position in field
            randomize: (o = {}) => {
                const x = Math.floor(Math.random() * width);
                const y = Math.floor(Math.random() * height);

                return {
                    x: x,
                    y: y,
                    xt: x,
                    yt: y,
                    age: o.age !== undefined ? o.age : 0,
                    m: 0
                };
            }
        };

        // Start animation
        this.start();
    }

    bilinearInterpolate(fx, fy, g00, g10, g01, g11) {
        const rx = 1 - fx;
        const ry = 1 - fy;

        const a = rx * ry;
        const b = fx * ry;
        const c = rx * fy;
        const d = fx * fy;

        const u = g00[0] * a + g10[0] * b + g01[0] * c + g11[0] * d;
        const v = g00[1] * a + g10[1] * b + g01[1] * c + g11[1] * d;
        const m = g00[2] * a + g10[2] * b + g01[2] * c + g11[2] * d;

        return [u, v, m];
    }

    getWaveAtPoint(lat, lon, waveData) {
        let nearest = null;
        let minDist = Infinity;

        for (const point of waveData) {
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

    waveToVector(direction, magnitude) {
        // Convert meteorological direction to velocity vector
        const rad = ((direction + 180) % 360) * Math.PI / 180;
        return {
            u: magnitude * Math.sin(rad) * this.options.velocityScale * 100,
            v: magnitude * Math.cos(rad) * this.options.velocityScale * 100
        };
    }

    start() {
        if (!this.field) return;

        // Initialize particles
        const particleCount = Math.round(
            this.canvas.width * this.canvas.height * this.options.particleMultiplier
        );

        this.particles = [];
        for (let i = 0; i < particleCount; i++) {
            this.particles.push(
                this.field.randomize({ age: Math.floor(Math.random() * this.options.particleAge) })
            );
        }

        // Start animation loop
        this.animate();
    }

    stop() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
    }

    animate() {
        const self = this;

        const frame = () => {
            self.animationFrame = requestAnimationFrame(frame);

            const now = Date.now();
            const delta = now - self.then;

            if (delta < 1000 / self.options.frameRate) {
                return;
            }

            self.then = now;
            self.evolve();
            self.draw();
        };

        frame();
    }

    evolve() {
        if (!this.field) return;

        this.particles.forEach(particle => {
            // Age particle
            if (particle.age > this.options.particleAge) {
                this.field.randomize(particle);
            }

            // Get velocity at current position
            const v = this.field.interpolate(particle.x, particle.y);
            if (!v) {
                this.field.randomize(particle);
                return;
            }

            const u = v[0];
            const vv = v[1];
            const m = v[2];

            // Calculate next position
            particle.xt = particle.x + u;
            particle.yt = particle.y + vv;
            particle.m = m;

            // Check if next position is valid
            if (this.field.isDefined(Math.round(particle.xt), Math.round(particle.yt))) {
                particle.x = particle.xt;
                particle.y = particle.yt;
                particle.age++;
            } else {
                // Hit boundary or land, respawn
                this.field.randomize(particle);
            }
        });
    }

    draw() {
        if (!this.ctx || !this.canvas) return;

        const ctx = this.ctx;
        const particles = this.particles;

        // Fade previous frame
        ctx.globalCompositeOperation = 'destination-in';
        ctx.fillStyle = `rgba(0, 0, 0, ${this.options.opacity})`;
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        ctx.globalCompositeOperation = 'source-over';
        ctx.globalAlpha = 1.0;
        ctx.lineWidth = this.options.lineWidth;

        // Draw particles
        particles.forEach(particle => {
            const color = this.colorFor(particle.m);
            ctx.strokeStyle = color;

            ctx.beginPath();
            ctx.moveTo(particle.x, particle.y);
            ctx.lineTo(particle.xt, particle.yt);
            ctx.stroke();
        });
    }

    colorFor(magnitude) {
        const colorScale = this.options.colorScale;
        const maxVelocity = this.options.maxVelocity;

        const index = Math.min(
            colorScale.length - 1,
            Math.floor((magnitude / maxVelocity) * colorScale.length)
        );

        return colorScale[Math.max(0, index)];
    }

    reset() {
        this.stop();
        if (this.ctx && this.canvas) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
        this.buildField();
    }

    resize() {
        const size = this.map.getSize();
        this.canvas.width = size.x;
        this.canvas.height = size.y;
        this.reset();
    }

    updateTime(timeIndex) {
        this.dataFetcher.setTimeIndex(timeIndex);
        this.reset();
    }

    remove() {
        this.stop();
        if (this.layer) {
            this.map.removeLayer(this.layer);
        }
    }
}
