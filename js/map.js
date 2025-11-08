/**
 * Main Map Application
 * Initializes Leaflet map and coordinates all components
 */

class WaveForecastApp {
    constructor() {
        this.map = null;
        this.dataFetcher = null;
        this.waveLayer = null;
        this.isPlaying = false;
        this.playInterval = null;
        this.currentTimeIndex = 0;
        this.forecastChart = null;  // Chart.js instance for wave forecast

        this.init();
    }

    /**
     * Initialize the application
     */
    async init() {
        this.updateStatus('Initializing map...');

        // Initialize map
        this.initMap();

        // Initialize data fetcher
        this.updateStatus('Loading wave forecast data...');
        this.dataFetcher = new GFSDataFetcher();
        await this.dataFetcher.initialize();

        // Initialize wave layer
        this.waveLayer = new WaveVelocityLayer(this.map, this.dataFetcher);
        this.waveLayer.startAnimation();

        // Setup controls
        this.setupControls();

        // Setup map interactions
        this.setupMapInteractions();

        // Initial draw
        this.updateTimeDisplay();
        this.updateStatus('Ready');
    }

    /**
     * Initialize Leaflet map
     */
    initMap() {
        // Create map centered on Pacific Ocean
        this.map = L.map('map', {
            center: [20, -160],
            zoom: 3,
            minZoom: 2,
            maxZoom: 8,
            zoomControl: true
        });

        // Add base tile layer
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
            subdomains: 'abcd',
            maxZoom: 20
        }).addTo(this.map);

        // Add scale control
        L.control.scale({
            imperial: true,
            metric: true
        }).addTo(this.map);
    }

    /**
     * Setup UI controls
     */
    setupControls() {
        const timeSteps = this.dataFetcher.getTimeSteps();

        // Time slider
        const slider = document.getElementById('time-slider');
        slider.max = timeSteps.length - 1;
        slider.value = 0;

        slider.addEventListener('input', (e) => {
            this.currentTimeIndex = parseInt(e.target.value);
            this.updateTime();
        });

        // Play/Pause buttons
        document.getElementById('play-btn').addEventListener('click', () => {
            this.play();
        });

        document.getElementById('pause-btn').addEventListener('click', () => {
            this.pause();
        });

        // Reset button
        document.getElementById('reset-btn').addEventListener('click', () => {
            this.reset();
        });

        // Vector toggle
        document.getElementById('toggle-vectors').addEventListener('change', (e) => {
            this.waveLayer.toggleVectors(e.target.checked);
        });

        // Particle toggle
        document.getElementById('toggle-particles').addEventListener('change', (e) => {
            this.waveLayer.toggleParticles(e.target.checked);
        });

        // Vector scale
        const scaleSlider = document.getElementById('vector-scale');
        const scaleValue = document.getElementById('vector-scale-value');

        scaleSlider.addEventListener('input', (e) => {
            const scale = parseFloat(e.target.value);
            scaleValue.textContent = scale.toFixed(1);
            this.waveLayer.setVectorScale(scale);
        });
    }

    /**
     * Setup map click interactions
     */
    setupMapInteractions() {
        this.map.on('click', (e) => {
            const lat = e.latlng.lat;
            const lon = e.latlng.lng;

            // Get wave data at clicked location
            const wave = this.dataFetcher.getWaveAtLocation(lat, lon, this.currentTimeIndex);

            if (wave) {
                // Show popup with wave information
                const content = `
                    <div style="min-width: 200px;">
                        <h3 style="margin: 0 0 10px 0; color: #64b5f6;">Wave Information</h3>
                        <p style="margin: 5px 0;"><strong>Height:</strong> ${wave.height.toFixed(2)} m</p>
                        <p style="margin: 5px 0;"><strong>Direction:</strong> ${wave.direction.toFixed(0)}° (${this.getDirectionName(wave.direction)})</p>
                        <p style="margin: 5px 0;"><strong>Period:</strong> ${wave.period.toFixed(1)} s</p>
                        <p style="margin: 5px 0;"><strong>Location:</strong> ${lat.toFixed(2)}°, ${lon.toFixed(2)}°</p>
                    </div>
                `;

                L.popup()
                    .setLatLng(e.latlng)
                    .setContent(content)
                    .openOn(this.map);

                // Update wave info panel
                this.updateWaveInfo(wave, lat, lon);

                // Show wave forecast chart
                this.showWaveForecastChart(lat, lon);
            } else {
                // Update wave info panel to show no data
                document.getElementById('wave-info').innerHTML = '<p>No wave data at this location</p>';
                // Hide chart section
                document.getElementById('forecast-chart-section').style.display = 'none';
            }
        });
    }

    /**
     * Update wave info panel
     */
    updateWaveInfo(wave, lat, lon) {
        const waveInfoDiv = document.getElementById('wave-info');
        waveInfoDiv.innerHTML = `
            <p><strong>Height:</strong> ${wave.height.toFixed(2)} m</p>
            <p><strong>Direction:</strong> ${wave.direction.toFixed(0)}° ${this.getDirectionName(wave.direction)}</p>
            <p><strong>Period:</strong> ${wave.period.toFixed(1)} s</p>
            <p><strong>Location:</strong><br>${lat.toFixed(2)}°, ${lon.toFixed(2)}°</p>
        `;
    }

    /**
     * Show wave forecast chart for a location
     */
    showWaveForecastChart(lat, lon) {
        const timeSteps = this.dataFetcher.getTimeSteps();
        const waveHeights = [];
        const wavePeriods = [];
        const labels = [];

        // Collect forecast data for all time steps
        for (let i = 0; i < timeSteps.length; i++) {
            const wave = this.dataFetcher.getWaveAtLocation(lat, lon, i);
            if (wave) {
                waveHeights.push(wave.height);
                wavePeriods.push(wave.period);
                labels.push(timeSteps[i].displayTime);
            }
        }

        // Show chart section
        document.getElementById('forecast-chart-section').style.display = 'block';

        // Destroy existing chart if it exists
        if (this.forecastChart) {
            this.forecastChart.destroy();
        }

        // Create new chart
        const ctx = document.getElementById('wave-forecast-chart').getContext('2d');
        this.forecastChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Wave Height (m)',
                        data: waveHeights,
                        borderColor: '#64b5f6',
                        backgroundColor: 'rgba(100, 181, 246, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Wave Period (s)',
                        data: wavePeriods,
                        borderColor: '#ffa726',
                        backgroundColor: 'rgba(255, 167, 38, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#fff',
                            font: {
                                size: 11
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: `Forecast at ${lat.toFixed(2)}°, ${lon.toFixed(2)}°`,
                        color: '#64b5f6',
                        font: {
                            size: 13
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#999',
                            font: {
                                size: 9
                            },
                            maxRotation: 45,
                            minRotation: 45
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Height (m)',
                            color: '#64b5f6',
                            font: {
                                size: 11
                            }
                        },
                        ticks: {
                            color: '#64b5f6',
                            font: {
                                size: 10
                            }
                        },
                        grid: {
                            color: 'rgba(100, 181, 246, 0.1)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Period (s)',
                            color: '#ffa726',
                            font: {
                                size: 11
                            }
                        },
                        ticks: {
                            color: '#ffa726',
                            font: {
                                size: 10
                            }
                        },
                        grid: {
                            drawOnChartArea: false,
                        }
                    }
                }
            }
        });
    }

    /**
     * Get compass direction name from degrees
     */
    getDirectionName(degrees) {
        const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
        const index = Math.round(((degrees % 360) / 22.5));
        return directions[index % 16];
    }

    /**
     * Update time display
     */
    updateTimeDisplay() {
        const timeSteps = this.dataFetcher.getTimeSteps();
        if (timeSteps.length > 0) {
            const currentTime = timeSteps[this.currentTimeIndex];
            document.getElementById('time-display').textContent = currentTime.displayTime;
        }
    }

    /**
     * Update time
     */
    updateTime() {
        this.waveLayer.updateTime(this.currentTimeIndex);
        this.updateTimeDisplay();
        document.getElementById('time-slider').value = this.currentTimeIndex;
    }

    /**
     * Play animation
     */
    play() {
        if (this.isPlaying) return;

        this.isPlaying = true;
        document.getElementById('play-btn').style.display = 'none';
        document.getElementById('pause-btn').style.display = 'inline-block';

        this.playInterval = setInterval(() => {
            const timeSteps = this.dataFetcher.getTimeSteps();
            this.currentTimeIndex = (this.currentTimeIndex + 1) % timeSteps.length;
            this.updateTime();
        }, 1000); // Update every second
    }

    /**
     * Pause animation
     */
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

    /**
     * Reset to first time step
     */
    reset() {
        this.pause();
        this.currentTimeIndex = 0;
        this.updateTime();
    }

    /**
     * Update status message
     */
    updateStatus(message) {
        document.getElementById('status').textContent = message;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new WaveForecastApp();
});
