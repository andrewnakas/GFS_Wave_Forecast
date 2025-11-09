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
        this.maxParticles = 1500;  // Increased for better wave visualization
        this.animationFrame = null;
        this.vectorScale = 5;
        this.showVectors = false;  // Disabled by default for instant loading
        this.showParticles = false;  // Disabled by default for instant loading
        this.frameSkip = 0;  // For throttling animation
        this.waveDataCache = null;  // Cache wave data
        this.cacheTimeIndex = -1;  // Track when cache is stale
        this.isMapMoving = false;  // Track if map is currently panning/zooming

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

                // Listen to map movement events for proper rendering
                map.on('movestart', () => this.onMoveStart());
                map.on('zoomstart', () => this.onMoveStart());
                map.on('moveend', () => this.onMoveEnd());
                map.on('zoomend', () => this.onMoveEnd());
                map.on('viewreset', () => this.onMoveEnd());
                map.on('resize', () => this.resize());

                this.initializeParticles();
            },

            onRemove: (map) => {
                L.DomUtil.remove(this.canvas);
                map.off('movestart');
                map.off('zoomstart');
                map.off('viewreset');
                map.off('moveend');
                map.off('zoomend');
                map.off('resize');
                this.stopAnimation();
            }
        });

        this.layer = new CanvasLayer();
        this.layer.addTo(this.map);
    }

    /**
     * Handle map movement start (pan/zoom start)
     */
    onMoveStart() {
        this.isMapMoving = true;
        // Clear canvas during movement
        if (this.ctx && this.canvas) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
    }

    /**
     * Handle map movement end (pan/zoom end)
     */
    onMoveEnd() {
        this.isMapMoving = false;
        // Redraw particles at their new screen positions
        this.redraw();
    }

    /**
     * Resize canvas
     */
    resize() {
        const size = this.map.getSize();
        this.canvas.width = size.x;
        this.canvas.height = size.y;
        // Don't reinitialize particles, just redraw at new positions
        this.redraw();
    }

    /**
     * Redraw canvas (without resetting particles)
     */
    redraw() {
        // Just redraw particles at their current geographic positions
        // Don't reset them
        this.draw();
    }

    /**
     * Initialize particles for animation
     */
    initializeParticles() {
        this.particles = [];
        const bounds = this.map.getBounds();

        // Store initial bounds for respawning reference
        this.initialBounds = bounds;

        for (let i = 0; i < this.maxParticles; i++) {
            let particle = this.createParticleInBounds(bounds);
            this.particles.push(particle);
        }
    }

    /**
     * Create a single particle within given bounds, avoiding land
     */
    createParticleInBounds(bounds) {
        let lat, lon;
        let attempts = 0;

        do {
            lat = bounds.getSouth() + Math.random() * (bounds.getNorth() - bounds.getSouth());
            lon = bounds.getWest() + Math.random() * (bounds.getEast() - bounds.getWest());
            attempts++;
        } while (this.dataFetcher.isLand(lat, lon) && attempts < 20);

        return {
            lat: lat,
            lon: lon,
            age: Math.random() * 100,
            maxAge: 50 + Math.random() * 50
        };
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

        // Don't draw if map is currently moving
        if (this.isMapMoving) return;

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

        // Draw wave vectors (much less frequently for maximum performance)
        if (this.showVectors && this.frameSkip % 5 === 0) {
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
        const spacing = 120; // Aggressively increased for maximum performance

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
        const speed = 0.015;  // Increased for longer wave movement

        // Create expanded bounds with buffer to prevent respawning during panning
        const latBuffer = (bounds.getNorth() - bounds.getSouth()) * 0.3;
        const lonBuffer = (bounds.getEast() - bounds.getWest()) * 0.3;
        const expandedBounds = L.latLngBounds(
            L.latLng(bounds.getSouth() - latBuffer, bounds.getWest() - lonBuffer),
            L.latLng(bounds.getNorth() + latBuffer, bounds.getEast() + lonBuffer)
        );

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

                // Only update particle position if map is NOT moving
                if (!this.isMapMoving) {
                    // Update particle position - move in wave direction
                    particle.lat += particle.vector.v * speed;
                    particle.lon += particle.vector.u * speed;
                }
            }

            // Only age and respawn particles if map is NOT moving
            if (this.isMapMoving) {
                // Skip aging and respawning during map movement
                // Just draw at current position
            } else {
                // Age particle
                particle.age++;

                // Check if particle is on land or out of bounds (use expanded bounds with buffer)
                const isOnLand = this.dataFetcher.isLand(particle.lat, particle.lon);
                const isOutOfBounds = !expandedBounds.contains([particle.lat, particle.lon]);

                // If particle is on land, respawn it at a nearby ocean location
                if (isOnLand) {
                    // Try to find ocean near the particle's current position
                    let newLat = particle.lat;
                    let newLon = particle.lon;
                    let found = false;

                    // Search in a spiral pattern around current position
                    for (let radius = 0.5; radius < 10 && !found; radius += 0.5) {
                        for (let angle = 0; angle < 360; angle += 30) {
                            const testLat = particle.lat + radius * Math.cos(angle * Math.PI / 180);
                            const testLon = particle.lon + radius * Math.sin(angle * Math.PI / 180);

                            if (!this.dataFetcher.isLand(testLat, testLon)) {
                                newLat = testLat;
                                newLon = testLon;
                                found = true;
                                break;
                            }
                        }
                    }

                    particle.lat = newLat;
                    particle.lon = newLon;
                    particle.age = 0;
                    particle.maxAge = 50 + Math.random() * 50;
                    particle.wave = null;
                    continue;  // Skip drawing this frame
                }

                // Reset particle if too old or way out of bounds
                if (particle.age > particle.maxAge || isOutOfBounds) {
                    // Only respawn within the expanded bounds to maintain stability
                    let attempts = 0;
                    let newParticle;

                    do {
                        newParticle = this.createParticleInBounds(expandedBounds);
                        attempts++;
                    } while (attempts < 20);

                    particle.lat = newParticle.lat;
                    particle.lon = newParticle.lon;
                    particle.age = 0;
                    particle.maxAge = newParticle.maxAge;
                    particle.wave = null;
                    continue;
                }
            }

            // Only draw if particle is within visible bounds (not in buffer zone)
            if (!bounds.contains([particle.lat, particle.lon])) {
                continue;  // Skip drawing particles outside visible area
            }

            // Draw particle as wave-like shape (elongated)
            const point = this.map.latLngToContainerPoint([particle.lat, particle.lon]);

            // Additional screen bounds check
            if (point.x < 0 || point.x > this.canvas.width || point.y < 0 || point.y > this.canvas.height) {
                continue;  // Skip if off-screen
            }

            const alpha = 1 - (particle.age / particle.maxAge);

            ctx.fillStyle = particle.wave ? this.getColorForHeight(particle.wave.height) : '#64b5f6';
            ctx.globalAlpha = alpha * 0.7;

            // Draw elongated wave-like shape moving broadside (perpendicular to direction)
            if (particle.vector) {
                // Calculate direction angle
                const angle = Math.atan2(particle.vector.v, particle.vector.u);
                // Rotate 90 degrees to move broadside like a wave crest
                const waveAngle = angle + Math.PI / 2;
                const waveLength = 12 + (particle.wave ? particle.wave.height * 3 : 6);
                const waveWidth = 3;

                ctx.save();
                ctx.translate(point.x, point.y);
                ctx.rotate(waveAngle);
                ctx.fillRect(-waveLength/2, -waveWidth/2, waveLength, waveWidth);
                ctx.restore();
            } else {
                // Fallback to simple circle
                ctx.fillRect(point.x - 2, point.y - 2, 4, 4);
            }
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
