/**
 * Wave Velocity Application
 * Main application controller
 */
class WaveVelocityApp {
    constructor() {
        this.map = null;
        this.waveData = null;
        this.field = null;
        this.particles = null;
        this.canvas = null;
        this.animationFrame = null;
        this.lastFrameTime = Date.now();
        this.frameRate = 15;
        this.currentTimeIndex = 0;
        this.isPlaying = false;
        this.playInterval = null;

        this.init();
    }

    async init() {
        console.log('Initializing Wave Velocity App...');

        // Update status
        this.updateStatus('Initializing map...');

        // Create map
        this.map = L.map('map', {
            center: [25, -160],
            zoom: 3,
            minZoom: 2,
            maxZoom: 7,
            zoomControl: true,
            attributionControl: true
        });

        // Add dark basemap with proper options
        const tileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 19,
            minZoom: 0,
            crossOrigin: true
        });

        tileLayer.on('tileerror', (error) => {
            console.warn('Tile load error:', error);
        });

        tileLayer.on('tileloadstart', () => {
            console.log('Tiles loading...');
        });

        tileLayer.on('load', () => {
            console.log('All tiles loaded');
        });

        tileLayer.addTo(this.map);

        // Generate wave data
        this.updateStatus('Generating wave data...');
        this.waveData = new WaveDataGenerator();

        // Wait for map to fully render and tiles to load
        await new Promise(resolve => {
            this.map.whenReady(() => {
                console.log('Map is ready');
                setTimeout(resolve, 200);
            });
        });

        // Create canvas overlay
        this.updateStatus('Building velocity field...');
        this.createCanvas();

        // Build velocity field
        this.field = new VelocityField(this.waveData, this.map, {
            velocityScale: 0.005
        });

        // Create particle system
        this.updateStatus('Initializing particles...');
        this.particles = new ParticleSystem(this.field, this.canvas, {
            particleAge: 90,
            lineWidth: 2,
            opacity: 0.97,
            maxVelocity: 10
        });

        // Setup event handlers
        this.setupEventHandlers();

        // Setup controls
        this.setupControls();

        // Start animation
        this.updateStatus('Ready');
        this.updateTimeDisplay();
        this.startAnimation();

        console.log('Wave Velocity App ready!');
    }

    createCanvas() {
        const size = this.map.getSize();

        this.canvas = document.createElement('canvas');
        this.canvas.width = size.x;
        this.canvas.height = size.y;
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '400';
        this.canvas.className = 'wave-velocity-canvas';

        // Append to map panes for proper layering
        const pane = this.map.getPanes().overlayPane;
        pane.appendChild(this.canvas);

        console.log(`Canvas created: ${size.x}x${size.y}, appended to map overlay pane`);
    }

    setupEventHandlers() {
        // Force a map invalidation to ensure tiles load
        this.map.invalidateSize();

        // Rebuild field on map move/zoom
        this.map.on('moveend', () => {
            console.log('Map moved, rebuilding field...');
            this.field.rebuild();
            this.particles.reset();
        });

        this.map.on('resize', () => {
            const size = this.map.getSize();
            this.canvas.width = size.x;
            this.canvas.height = size.y;
            this.field.rebuild();
            this.particles.resize(size.x, size.y);
        });

        // Handle zoom end to reload tiles if needed
        this.map.on('zoomend', () => {
            this.map.invalidateSize();
        });
    }

    setupControls() {
        const timeSteps = this.waveData.getTimeSteps();
        const slider = document.getElementById('time-slider');

        slider.max = timeSteps.length - 1;
        slider.value = 0;

        slider.addEventListener('input', (e) => {
            this.currentTimeIndex = parseInt(e.target.value);
            this.updateTime();
        });

        document.getElementById('play-btn').addEventListener('click', () => {
            this.play();
        });

        document.getElementById('pause-btn').addEventListener('click', () => {
            this.pause();
        });

        document.getElementById('reset-btn').addEventListener('click', () => {
            this.reset();
        });
    }

    updateStatus(message) {
        const display = document.getElementById('time-display');
        if (display) {
            display.textContent = message;
        }
    }

    updateTimeDisplay() {
        const timeSteps = this.waveData.getTimeSteps();
        const current = timeSteps[this.currentTimeIndex];

        const display = document.getElementById('time-display');
        if (display && current) {
            display.textContent = current.display;
        }
    }

    updateTime() {
        this.field.setTime(this.currentTimeIndex);
        this.particles.reset();
        this.updateTimeDisplay();
    }

    play() {
        if (this.isPlaying) return;

        this.isPlaying = true;
        document.getElementById('play-btn').style.display = 'none';
        document.getElementById('pause-btn').style.display = 'inline-block';

        const timeSteps = this.waveData.getTimeSteps();

        this.playInterval = setInterval(() => {
            this.currentTimeIndex = (this.currentTimeIndex + 1) % timeSteps.length;
            document.getElementById('time-slider').value = this.currentTimeIndex;
            this.updateTime();
        }, 1000);
    }

    pause() {
        if (!this.isPlaying) return;

        this.isPlaying = false;
        document.getElementById('play-btn').style.display = 'inline-block';
        document.getElementById('pause-btn').style.display = 'none';

        if (this.playInterval) {
            clearInterval(this.playInterval);
            this.playInterval = null;
        }
    }

    reset() {
        this.pause();
        this.currentTimeIndex = 0;
        document.getElementById('time-slider').value = 0;
        this.updateTime();
    }

    startAnimation() {
        const animate = () => {
            this.animationFrame = requestAnimationFrame(animate);

            const now = Date.now();
            const elapsed = now - this.lastFrameTime;

            // Throttle to frameRate
            if (elapsed < 1000 / this.frameRate) {
                return;
            }

            this.lastFrameTime = now;

            // Evolve and draw particles
            this.particles.evolve();
            this.particles.draw();
        };

        animate();
    }

    stop() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
        this.pause();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.waveApp = new WaveVelocityApp();
});
