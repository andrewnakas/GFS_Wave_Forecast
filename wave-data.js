// Load GFS wave data for leaflet-velocity
(function() {
    'use strict';

    // Try to load real GFS data, fallback to synthetic if unavailable
    async function loadWaveData() {
        console.log('Loading wave data...');

        try {
            // Try to load pre-fetched GFS data
            const response = await fetch('gfs-wave-data.json');

            if (response.ok) {
                const data = await response.json();
                console.log('Loaded real GFS wave data');
                console.log(`Grid: ${data[0].header.nx} x ${data[0].header.ny}`);
                console.log(`Data points: ${data[0].data.length}`);
                return data;
            } else {
                throw new Error('GFS data file not found');
            }
        } catch (error) {
            console.warn('Could not load GFS data:', error.message);
            console.log('Using synthetic wave data');
            return generateSyntheticData();
        }
    }

    // Generate synthetic data as fallback
    function generateSyntheticData() {
        const dx = 2.5;
        const dy = 2.5;
        const nx = 144;  // 360 / 2.5
        const ny = 73;   // 180 / 2.5 + 1
        const la1 = 90;
        const la2 = -90;
        const lo1 = 0;
        const lo2 = 357.5;

        const uData = [];
        const vData = [];

        console.log('Generating synthetic wave data...');

        // Generate grid from north to south, west to east
        for (let y = 0; y < ny; y++) {
            const lat = la1 - (y * dy);

            for (let x = 0; x < nx; x++) {
                const lon = lo1 + (x * dx);

                // Simulate realistic wave patterns
                let u = 0;
                let v = 0;

                // Southern Ocean (strong westerlies)
                if (lat < -40) {
                    u = 5 + Math.cos(lon * Math.PI / 180) * 2;
                    v = Math.sin(lon * Math.PI / 180) * 1.5;
                }
                // Mid-latitude westerlies (30-60°)
                else if ((lat > 30 && lat < 60) || (lat > -40 && lat < -30)) {
                    u = 3 + Math.cos(lon * Math.PI / 180) * 1.5;
                    v = Math.sin(lon * Math.PI / 180);
                }
                // Trade winds (15-30°)
                else if ((lat > 15 && lat < 30) || (lat > -30 && lat < -15)) {
                    u = -2.5 + Math.sin(lon * Math.PI / 180) * 0.8;
                    v = -0.5 + Math.cos(lon * Math.PI / 180) * 0.3;
                }
                // Equatorial (light and variable)
                else if (lat > -15 && lat < 15) {
                    u = Math.sin(lon * Math.PI / 90) * 1.2;
                    v = Math.cos(lon * Math.PI / 90) * 0.6;
                }
                // Polar
                else {
                    u = Math.sin(lon * Math.PI / 60);
                    v = -Math.cos(lon * Math.PI / 60) * 0.8;
                }

                // Add realistic variation
                u += (Math.random() - 0.5) * 0.4;
                v += (Math.random() - 0.5) * 0.4;

                // Add wave-like patterns
                const wavePhase = (lat * 3 + lon * 2) * Math.PI / 180;
                u += Math.sin(wavePhase) * 0.3;
                v += Math.cos(wavePhase) * 0.2;

                uData.push(u);
                vData.push(v);
            }
        }

        console.log(`Generated ${uData.length} synthetic data points`);

        return [
            {
                "header": {
                    "parameterCategory": 2,
                    "parameterNumber": 2,
                    "dx": dx,
                    "dy": dy,
                    "nx": nx,
                    "ny": ny,
                    "la1": la1,
                    "la2": la2,
                    "lo1": lo1,
                    "lo2": lo2
                },
                "data": uData
            },
            {
                "header": {
                    "parameterCategory": 2,
                    "parameterNumber": 3,
                    "dx": dx,
                    "dy": dy,
                    "nx": nx,
                    "ny": ny,
                    "la1": la1,
                    "la2": la2,
                    "lo1": lo1,
                    "lo2": lo2
                },
                "data": vData
            }
        ];
    }

    // Initialize and expose data
    async function init() {
        window.waveData = await loadWaveData();
        console.log('Wave data ready');
        window.dispatchEvent(new Event('waveDataReady'));
    }

    init();
})();
