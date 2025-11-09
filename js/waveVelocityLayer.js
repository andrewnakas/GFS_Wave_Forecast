/**
 * Wave Velocity Layer - Based on leaflet-velocity
 * Implements smooth particle flow visualization for wave data
 */

class WaveVelocityLayer {
    constructor(map, dataFetcher, options = {}) {
        this.map = map;
        this.dataFetcher = dataFetcher;

        // Configuration matching leaflet-velocity
        this.options = Object.assign({
            displayValues: true,
            displayOptions: {
                velocityType: 'Wave',
                displayPosition: 'bottomleft',
                displayEmptyString: 'No wave data'
            },
            maxVelocity: 10, // m/s
            velocityScale: 0.005, // Particle speed modifier
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
            particleMultiplier: 1/300, // Particle density
            particleAge: 90, // Max age in frames
            lineWidth: 2,
            opacity: 0.97
        }, options);

        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.animationFrame = null;
        this.field = null;
        this.colorStyles = [];
        this.buckets = [];

        this.initializeCanvas();
        this.buildColorScale();
    }

    /**
     * Initialize canvas overlay
     */
    initializeCanvas() {
        const CanvasLayer = L.Layer.extend({
            onAdd: (map) => {
                this.canvas = L.DomUtil.create('canvas', 'wave-velocity-canvas');
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
                map.on('mousemove', (e) => this.onMouseMove(e));

                this.buildField();
                this.start();
            },

            onRemove: (map) => {
                this.stop();
                L.DomUtil.remove(this.canvas);
                map.off('moveend');
                map.off('resize');
                map.off('mousemove');
            }
        });

        this.layer = new CanvasLayer();
        this.layer.addTo(this.map);
    }

    /**
     * Build wave field with bilinear interpolation
     */
    buildField() {
        const bounds = this.map.getBounds();
        const width = this.canvas.width;
        const height = this.canvas.height;

        const data = this.dataFetcher.getDataForTime(this.dataFetcher.currentTimeIndex);
        if (!data) return null;

        // Create interpolated field
        const field = [];
        const velocityScale = this.options.velocityScale;

        for (let y = 0; y < height; y += 4) {
            field[y] = [];
            for (let x = 0; x < width; x += 4) {
                const latLng = this.map.containerPointToLatLng([x, y]);
                const wave = this.getInterpolatedWave(latLng.lat, latLng.lng, data);

                if (wave) {
                    // Convert wave direction to velocity vector
                    const vector = this.directionToVector(wave.direction, wave.height);
                    field[y][x] = [vector.u * velocityScale * 100, vector.v * velocityScale * 100, wave.height];
                } else {
                    field[y][x] = [0, 0, 0];
                }
            }
        }

        this.field = {
            width: width,
            height: height,
            data: field,
            interpolate: (x, y) => this.bilinearInterpolate(x, y, field, width, height),
            randomize: (particle) => {
                const x = Math.floor(Math.random() * width);
                const y = Math.floor(Math.random() * height);
                return {
                    x: x,
                    y: y,
                    xt: x,
                    yt: y,
                    age: particle.age || 0,
                    intensity: 0
                };
            },
            isValid: (x, y) => {
                if (x < 0 || x >= width || y < 0 || y >= height) return false;
                const latLng = this.map.containerPointToLatLng([x, y]);
                return !this.dataFetcher.isLand(latLng.lat, latLng.lng);
            }
        };
    }

    /**
     * Bilinear interpolation for smooth field
     */
    bilinearInterpolate(x, y, field, width, height) {
        const x0 = Math.floor(x / 4) * 4;
        const y0 = Math.floor(y / 4) * 4;
        const x1 = Math.min(x0 + 4, width - 1);
        const y1 = Math.min(y0 + 4, height - 1);

        const fx = (x - x0) / 4;
        const fy = (y - y0) / 4;

        if (!field[y0] || !field[y1]) return [0, 0, 0];

        const g00 = field[y0][x0] || [0, 0, 0];
        const g10 = field[y0][x1] || [0, 0, 0];
        const g01 = field[y1][x0] || [0, 0, 0];
        const g11 = field[y1][x1] || [0, 0, 0];

        const rx = 1 - fx;
        const ry = 1 - fy;
        const a = rx * ry;
        const b = fx * ry;
        const c = rx * fy;
        const d = fx * fy;

        const u = g00[0] * a + g10[0] * b + g01[0] * c + g11[0] * d;
        const v = g00[1] * a + g10[1] * b + g01[1] * c + g11[1] * d;
        const magnitude = g00[2] * a + g10[2] * b + g01[2] * c + g11[2] * d;

        return [u, v, magnitude];
    }

    /**
     * Get interpolated wave data at location
     */
    getInterpolatedWave(lat, lon, data) {
        // Find nearest grid points
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
     * Convert direction to vector (u, v)
     */
    directionToVector(direction, magnitude) {
        // Direction is "coming from" in meteorological convention
        const radians = (direction + 180) % 360 * Math.PI / 180;
        return {
            u: magnitude * Math.sin(radians),
            v: magnitude * Math.cos(radians)
        };
    }

    /**
     * Build color scale for particles
     */
    buildColorScale() {
        const colorScale = this.options.colorScale;
        const maxVelocity = this.options.maxVelocity;

        this.colorStyles = colorScale.map((color, i) => {
            return {
                style: color,
                min: i * maxVelocity / colorScale.length,
                max: (i + 1) * maxVelocity / colorScale.length
            };
        });
    }

    /**
     * Get color for magnitude
     */
    getColor(magnitude) {
        for (let i = this.colorStyles.length - 1; i >= 0; i--) {
            if (magnitude >= this.colorStyles[i].min) {
                return this.colorStyles[i].style;
            }
        }
        return this.colorStyles[0].style;
    }

    /**
     * Start animation
     */
    start() {
        if (!this.field) this.buildField();
        if (!this.field) return;

        // Initialize particles
        const particleCount = Math.round(this.canvas.width * this.canvas.height * this.options.particleMultiplier);
        this.particles = [];

        // Create particles distributed by color buckets
        const bucketsPerColor = Math.ceil(particleCount / this.options.colorScale.length);

        for (let i = 0; i < particleCount; i++) {
            this.particles.push(this.field.randomize({
                age: Math.floor(Math.random() * this.options.particleAge)
            }));
        }

        this.animate();
    }

    /**
     * Stop animation
     */
    stop() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
    }

    /**
     * Main animation loop
     */
    animate() {
        const then = Date.now();

        const frame = () => {
            this.animationFrame = requestAnimationFrame(frame);

            const now = Date.now();
            const delta = now - then;

            if (delta < 1000 / this.options.frameRate) return;

            this.evolve();
            this.draw();
        };

        frame();
    }

    /**
     * Evolve particles
     */
    evolve() {
        if (!this.field) return;

        this.particles.forEach(particle => {
            if (particle.age > this.options.particleAge) {
                this.field.randomize(particle);
            }

            const x = particle.x;
            const y = particle.y;

            const v = this.field.interpolate(x, y);
            const u = v[0];
            const vv = v[1];
            const magnitude = v[2];

            particle.xt = x + u;
            particle.yt = y + vv;
            particle.intensity = magnitude;

            // Check if next position is valid
            if (this.field.isValid(Math.round(particle.xt), Math.round(particle.yt))) {
                particle.x = particle.xt;
                particle.y = particle.yt;
                particle.age++;
            } else {
                // Particle hit land or boundary, respawn
                this.field.randomize(particle);
            }
        });
    }

    /**
     * Draw particles on canvas
     */
    draw() {
        if (!this.ctx) return;

        const ctx = this.ctx;
        const particles = this.particles;
        const opacity = this.options.opacity;

        // Fade previous frame
        ctx.globalCompositeOperation = 'destination-in';
        ctx.fillStyle = `rgba(0, 0, 0, ${opacity})`;
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        ctx.globalCompositeOperation = 'source-over';

        // Draw particles
        ctx.lineWidth = this.options.lineWidth;

        particles.forEach(particle => {
            const color = this.getColor(particle.intensity);
            ctx.strokeStyle = color;

            ctx.beginPath();
            ctx.moveTo(particle.x, particle.y);
            ctx.lineTo(particle.xt, particle.yt);
            ctx.stroke();
        });
    }

    /**
     * Reset field on map movement
     */
    reset() {
        this.stop();
        this.buildField();
        this.start();
    }

    /**
     * Resize canvas
     */
    resize() {
        const size = this.map.getSize();
        this.canvas.width = size.x;
        this.canvas.height = size.y;
        this.reset();
    }

    /**
     * Handle mouse movement to display wave info
     */
    onMouseMove(e) {
        if (!this.options.displayValues) return;
        if (!this.field) return;

        const point = this.map.latLngToContainerPoint(e.latlng);
        const v = this.field.interpolate(point.x, point.y);

        if (v[2] > 0) {
            const magnitude = v[2].toFixed(2);
            // Display could be added here
        }
    }

    /**
     * Update time index
     */
    updateTime(timeIndex) {
        this.dataFetcher.setTimeIndex(timeIndex);
        this.reset();
    }

    /**
     * Remove layer
     */
    remove() {
        this.stop();
        if (this.layer) {
            this.map.removeLayer(this.layer);
        }
    }
}
