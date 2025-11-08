/**
 * Wave Velocity Layer
 * Renders animated wave vectors on Leaflet map
 */

class WaveVelocityLayer {
    constructor(map, dataFetcher) {
        this.map = map;
        this.dataFetcher = dataFetcher;
        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.maxParticles = 3000;
        this.animationFrame = null;
        this.vectorScale = 5;
        this.showVectors = true;
        this.showParticles = true;

        this.initializeCanvas();
    }

    /**
     * Initialize canvas overlay
     */
    initializeCanvas() {
        // Create canvas overlay
        const CanvasLayer = L.Layer.extend({
            onAdd: (map) => {
                this.canvas = L.DomUtil.create('canvas', 'wave-canvas');
                this.ctx = this.canvas.getContext('2d');

                // Size canvas to map
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

                this.initializeParticles();
            },

            onRemove: (map) => {
                L.DomUtil.remove(this.canvas);
                map.off('moveend', this.reset);
                map.off('resize', this.resize);
                this.stopAnimation();
            }
        });

        this.layer = new CanvasLayer();
        this.layer.addTo(this.map);
    }

    /**
     * Resize canvas
     */
    resize() {
        const size = this.map.getSize();
        this.canvas.width = size.x;
        this.canvas.height = size.y;
        this.initializeParticles();
    }

    /**
     * Reset layer
     */
    reset() {
        this.initializeParticles();
    }

    /**
     * Initialize particles for animation
     */
    initializeParticles() {
        this.particles = [];
        const bounds = this.map.getBounds();

        for (let i = 0; i < this.maxParticles; i++) {
            this.particles.push({
                lat: bounds.getSouth() + Math.random() * (bounds.getNorth() - bounds.getSouth()),
                lon: bounds.getWest() + Math.random() * (bounds.getEast() - bounds.getWest()),
                age: Math.random() * 100,
                maxAge: 50 + Math.random() * 50
            });
        }
    }

    /**
     * Start animation
     */
    startAnimation() {
        if (this.animationFrame) return;

        const animate = () => {
            this.draw();
            this.animationFrame = requestAnimationFrame(animate);
        };

        animate();
    }

    /**
     * Stop animation
     */
    stopAnimation() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
    }

    /**
     * Draw wave vectors and particles
     */
    draw() {
        if (!this.ctx || !this.canvas) return;

        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        const bounds = this.map.getBounds();
        const timeIndex = this.dataFetcher.currentTimeIndex;
        const waveData = this.dataFetcher.getDataForTime(timeIndex);

        if (!waveData) return;

        // Draw wave vectors
        if (this.showVectors) {
            this.drawVectors(waveData, bounds);
        }

        // Draw and update particles
        if (this.showParticles) {
            this.updateAndDrawParticles(waveData, bounds);
        }
    }

    /**
     * Draw wave vectors as arrows
     */
    drawVectors(waveData, bounds) {
        const spacing = 50; // pixels between vectors

        for (let x = 0; x < this.canvas.width; x += spacing) {
            for (let y = 0; y < this.canvas.height; y += spacing) {
                const point = this.map.containerPointToLatLng([x, y]);
                const lat = point.lat;
                const lon = point.lng;

                // Check if point is in bounds
                if (!bounds.contains(point)) continue;

                // Get wave data at this point
                const wave = this.dataFetcher.getWaveAtLocation(lat, lon);
                if (!wave) continue;

                // Convert direction to vector
                const vector = this.dataFetcher.directionToVector(
                    wave.direction,
                    wave.height
                );

                // Draw arrow
                this.drawArrow(
                    x, y,
                    vector.u * this.vectorScale,
                    vector.v * this.vectorScale,
                    this.getColorForHeight(wave.height),
                    wave.height
                );
            }
        }
    }

    /**
     * Draw arrow
     */
    drawArrow(x, y, u, v, color, magnitude) {
        const ctx = this.ctx;
        const arrowLength = Math.sqrt(u * u + v * v);

        if (arrowLength < 2) return;

        ctx.save();

        // Set style based on magnitude
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = Math.max(1, Math.min(3, magnitude * 0.5));
        ctx.globalAlpha = 0.7;

        // Draw line
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + u, y - v); // Flip v for canvas coordinates
        ctx.stroke();

        // Draw arrowhead
        const angle = Math.atan2(-v, u);
        const headLength = Math.min(arrowLength * 0.3, 10);

        ctx.beginPath();
        ctx.moveTo(x + u, y - v);
        ctx.lineTo(
            x + u - headLength * Math.cos(angle - Math.PI / 6),
            y - v + headLength * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
            x + u - headLength * Math.cos(angle + Math.PI / 6),
            y - v + headLength * Math.sin(angle + Math.PI / 6)
        );
        ctx.closePath();
        ctx.fill();

        ctx.restore();
    }

    /**
     * Update and draw particles
     */
    updateAndDrawParticles(waveData, bounds) {
        const ctx = this.ctx;

        for (let particle of this.particles) {
            // Get wave at particle location
            const wave = this.dataFetcher.getWaveAtLocation(particle.lat, particle.lon);

            if (wave) {
                // Update particle position based on wave
                const vector = this.dataFetcher.directionToVector(
                    wave.direction,
                    wave.height
                );

                const speed = 0.002;
                particle.lat += vector.v * speed;
                particle.lon += vector.u * speed;
            }

            // Age particle
            particle.age++;

            // Reset particle if too old or out of bounds
            if (particle.age > particle.maxAge || !bounds.contains([particle.lat, particle.lon])) {
                particle.lat = bounds.getSouth() + Math.random() * (bounds.getNorth() - bounds.getSouth());
                particle.lon = bounds.getWest() + Math.random() * (bounds.getEast() - bounds.getWest());
                particle.age = 0;
                particle.maxAge = 50 + Math.random() * 50;
            }

            // Draw particle
            const point = this.map.latLngToContainerPoint([particle.lat, particle.lon]);
            const alpha = 1 - (particle.age / particle.maxAge);

            ctx.save();
            ctx.fillStyle = wave ? this.getColorForHeight(wave.height) : '#64b5f6';
            ctx.globalAlpha = alpha * 0.6;
            ctx.beginPath();
            ctx.arc(point.x, point.y, 2, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        }
    }

    /**
     * Get color based on wave height
     */
    getColorForHeight(height) {
        // Color scale from blue (low) to red (high)
        if (height < 1) return '#0a1929';
        if (height < 2) return '#1565c0';
        if (height < 3) return '#1976d2';
        if (height < 4) return '#42a5f5';
        if (height < 5) return '#ffa726';
        if (height < 6) return '#ff9800';
        if (height < 7) return '#f57c00';
        return '#d32f2f';
    }

    /**
     * Update time index and redraw
     */
    updateTime(timeIndex) {
        this.dataFetcher.setTimeIndex(timeIndex);
        this.draw();
    }

    /**
     * Set vector scale
     */
    setVectorScale(scale) {
        this.vectorScale = scale;
        this.draw();
    }

    /**
     * Toggle vectors visibility
     */
    toggleVectors(show) {
        this.showVectors = show;
        this.draw();
    }

    /**
     * Toggle particles visibility
     */
    toggleParticles(show) {
        this.showParticles = show;
        if (!show) {
            this.particles = [];
        } else {
            this.initializeParticles();
        }
        this.draw();
    }

    /**
     * Remove layer
     */
    remove() {
        this.stopAnimation();
        if (this.layer) {
            this.map.removeLayer(this.layer);
        }
    }
}
