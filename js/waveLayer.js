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
        this.maxParticles = 800;  // Reduced from 3000 for better performance
        this.animationFrame = null;
        this.vectorScale = 5;
        this.showVectors = true;
        this.showParticles = true;
        this.frameSkip = 0;  // For throttling animation
        this.waveDataCache = null;  // Cache wave data
        this.cacheTimeIndex = -1;  // Track when cache is stale

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

        // Frame skipping for better performance - only draw every other frame
        this.frameSkip++;
        if (this.frameSkip % 2 !== 0 && !this.showVectors) {
            // Skip this frame for particle-only mode
            return;
        }

        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        const bounds = this.map.getBounds();
        const timeIndex = this.dataFetcher.currentTimeIndex;

        // Cache wave data to avoid regenerating it every frame
        if (this.cacheTimeIndex !== timeIndex) {
            this.waveDataCache = this.dataFetcher.getDataForTime(timeIndex);
            this.cacheTimeIndex = timeIndex;
        }

        if (!this.waveDataCache) return;

        // Draw wave vectors (less frequently)
        if (this.showVectors && this.frameSkip % 3 === 0) {
            this.drawVectors(this.waveDataCache, bounds);
        }

        // Draw and update particles (every frame for smooth animation)
        if (this.showParticles) {
            this.updateAndDrawParticles(this.waveDataCache, bounds);
        }
    }

    /**
     * Draw wave vectors as arrows
     */
    drawVectors(waveData, bounds) {
        const spacing = 80; // Increased from 50 for better performance

        // Calculate start positions to center the grid
        const startX = spacing / 2;
        const startY = spacing / 2;

        for (let x = startX; x < this.canvas.width; x += spacing) {
            for (let y = startY; y < this.canvas.height; y += spacing) {
                const point = this.map.containerPointToLatLng([x, y]);

                // Check if point is in bounds first (faster check)
                if (!bounds.contains(point)) continue;

                const lat = point.lat;
                const lon = point.lng;

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
        const speed = 0.002;

        // Batch drawing operations for better performance
        ctx.save();

        for (let i = 0; i < this.particles.length; i++) {
            const particle = this.particles[i];

            // Only update wave data every 5 frames per particle for performance
            if (!particle.wave || this.frameSkip % 5 === i % 5) {
                particle.wave = this.dataFetcher.getWaveAtLocation(particle.lat, particle.lon);
            }

            if (particle.wave) {
                // Cache the vector conversion
                if (!particle.vector || this.frameSkip % 5 === i % 5) {
                    particle.vector = this.dataFetcher.directionToVector(
                        particle.wave.direction,
                        particle.wave.height
                    );
                }

                // Update particle position
                particle.lat += particle.vector.v * speed;
                particle.lon += particle.vector.u * speed;
            }

            // Age particle
            particle.age++;

            // Reset particle if too old or out of bounds
            if (particle.age > particle.maxAge || !bounds.contains([particle.lat, particle.lon])) {
                particle.lat = bounds.getSouth() + Math.random() * (bounds.getNorth() - bounds.getSouth());
                particle.lon = bounds.getWest() + Math.random() * (bounds.getEast() - bounds.getWest());
                particle.age = 0;
                particle.maxAge = 50 + Math.random() * 50;
                particle.wave = null;  // Force wave update on reset
                continue;
            }

            // Draw particle (batched)
            const point = this.map.latLngToContainerPoint([particle.lat, particle.lon]);
            const alpha = 1 - (particle.age / particle.maxAge);

            ctx.fillStyle = particle.wave ? this.getColorForHeight(particle.wave.height) : '#64b5f6';
            ctx.globalAlpha = alpha * 0.6;
            ctx.fillRect(point.x - 1, point.y - 1, 2, 2);  // Use fillRect instead of arc for speed
        }

        ctx.restore();
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
