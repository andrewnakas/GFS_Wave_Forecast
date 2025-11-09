/**
 * Particle System
 * Manages particle lifecycle and animation
 */
class ParticleSystem {
    constructor(field, canvas, options = {}) {
        this.field = field;
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');

        this.options = Object.assign({
            particleAge: 90,
            particleCount: Math.round(canvas.width * canvas.height / 300),
            lineWidth: 2,
            opacity: 0.97,
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
            maxVelocity: 10
        }, options);

        this.particles = [];
        this.animating = false;

        this.init();
    }

    init() {
        // Create particles
        this.particles = [];
        for (let i = 0; i < this.options.particleCount; i++) {
            this.particles.push(this.createParticle());
        }
        console.log(`Created ${this.particles.length} particles`);
    }

    createParticle() {
        const width = this.canvas.width;
        const height = this.canvas.height;

        // Random position
        let x, y;
        let attempts = 0;

        do {
            x = Math.random() * width;
            y = Math.random() * height;
            attempts++;
        } while (!this.field.isValid(x, y) && attempts < 10);

        return {
            x: x,
            y: y,
            age: Math.random() * this.options.particleAge,
            xt: x,
            yt: y,
            m: 0
        };
    }

    evolve() {
        const maxAge = this.options.particleAge;
        let movedCount = 0;
        let respawnedCount = 0;

        for (let i = 0; i < this.particles.length; i++) {
            const p = this.particles[i];

            // Age particle
            p.age++;

            // Respawn if too old
            if (p.age > maxAge) {
                Object.assign(p, this.createParticle());
                respawnedCount++;
                continue;
            }

            // Get velocity at current position
            const v = this.field.interpolate(p.x, p.y);

            if (!v || (v.u === 0 && v.v === 0)) {
                // No velocity, respawn
                Object.assign(p, this.createParticle());
                respawnedCount++;
                continue;
            }

            // Calculate next position (don't update x,y yet - do it after drawing)
            p.xt = p.x + v.u;
            p.yt = p.y + v.v;
            p.m = v.m;

            // Check if next position is valid
            if (!this.field.isValid(Math.round(p.xt), Math.round(p.yt))) {
                // Hit land or boundary, respawn
                Object.assign(p, this.createParticle());
                respawnedCount++;
            } else {
                movedCount++;
            }
        }

        // Log every 60 frames (4 seconds at 15fps)
        if (this.evolveCount === undefined) this.evolveCount = 0;
        this.evolveCount++;
        if (this.evolveCount % 60 === 0) {
            console.log(`Particles - moved: ${movedCount}, respawned: ${respawnedCount}`);
        }
    }

    draw() {
        const ctx = this.ctx;
        const particles = this.particles;
        const colorScale = this.options.colorScale;
        const maxVelocity = this.options.maxVelocity;

        // Fade previous frame
        ctx.globalCompositeOperation = 'destination-in';
        ctx.fillStyle = `rgba(0, 0, 0, ${this.options.opacity})`;
        ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw new particles
        ctx.globalCompositeOperation = 'source-over';
        ctx.lineWidth = this.options.lineWidth;
        ctx.globalAlpha = 1.0;

        let drawnCount = 0;

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];

            // Skip if no movement (but this should be rare now)
            const dx = p.xt - p.x;
            const dy = p.yt - p.y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < 0.01) continue;

            // Get color based on magnitude
            const colorIndex = Math.min(
                colorScale.length - 1,
                Math.floor((p.m / maxVelocity) * colorScale.length)
            );
            ctx.strokeStyle = colorScale[Math.max(0, colorIndex)];

            // Draw line from current to next position
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p.xt, p.yt);
            ctx.stroke();

            // NOW update position for next frame
            p.x = p.xt;
            p.y = p.yt;

            drawnCount++;
        }

        // Log first few frames to verify drawing
        if (!this.drawCount) this.drawCount = 0;
        this.drawCount++;
        if (this.drawCount <= 5) {
            console.log(`Frame ${this.drawCount}: Drew ${drawnCount} particles, first particle moved ${dist.toFixed(2)}px`);
        }
    }

    resize(width, height) {
        this.canvas.width = width;
        this.canvas.height = height;
        this.options.particleCount = Math.round(width * height / 300);
        this.init();
    }

    reset() {
        this.init();
    }
}
