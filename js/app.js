/**
 * Wave Velocity Application
 * Minimal setup matching leaflet-velocity demo
 */

class WaveApp {
    constructor() {
        this.map = null;
        this.dataFetcher = null;
        this.velocityLayer = null;
        this.currentTimeIndex = 0;
        this.isPlaying = false;
        this.playInterval = null;

        this.init();
    }

    async init() {
        // Initialize map with dark tiles
        this.map = L.map('map', {
            center: [20, -160],
            zoom: 3,
            minZoom: 2,
            maxZoom: 8,
            zoomControl: true
        });

        // Dark basemap matching leaflet-velocity demo
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(this.map);

        // Initialize data fetcher
        this.dataFetcher = new GFSDataFetcher();
        await this.dataFetcher.initialize();

        // Create velocity layer with leaflet-velocity options
        this.velocityLayer = new WaveVelocityLayer(this.map, this.dataFetcher, {
            displayValues: true,
            maxVelocity: 10, // 10 m wave height max
            velocityScale: 0.005,
            frameRate: 15,
            particleMultiplier: 1/300,
            particleAge: 90,
            lineWidth: 2,
            opacity: 0.97
        });

        // Setup controls
        this.setupControls();

        // Initial time display
        this.updateTimeDisplay();
    }

    setupControls() {
        const timeSteps = this.dataFetcher.getTimeSteps();
        const slider = document.getElementById('time-slider');
        slider.max = timeSteps.length - 1;

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

    updateTimeDisplay() {
        const timeSteps = this.dataFetcher.getTimeSteps();
        if (timeSteps.length > 0) {
            const currentTime = timeSteps[this.currentTimeIndex];
            document.getElementById('time-display').textContent = currentTime.displayTime;
        }
    }

    updateTime() {
        this.velocityLayer.updateTime(this.currentTimeIndex);
        this.updateTimeDisplay();
        document.getElementById('time-slider').value = this.currentTimeIndex;
    }

    play() {
        if (this.isPlaying) return;

        this.isPlaying = true;
        document.getElementById('play-btn').style.display = 'none';
        document.getElementById('pause-btn').style.display = 'inline-block';

        this.playInterval = setInterval(() => {
            const timeSteps = this.dataFetcher.getTimeSteps();
            this.currentTimeIndex = (this.currentTimeIndex + 1) % timeSteps.length;
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
        this.updateTime();
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new WaveApp();
});
