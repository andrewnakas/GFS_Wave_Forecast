// Generate wave velocity data in leaflet-velocity format
(function() {
    'use strict';

    // Grid parameters - matching leaflet-velocity demo format
    const dx = 2.5;  // longitude spacing
    const dy = 2.5;  // latitude spacing
    const nx = 144;  // 360 / 2.5
    const ny = 73;   // 180 / 2.5 + 1
    const la1 = 90;  // north
    const la2 = -90; // south
    const lo1 = 0;   // west
    const lo2 = 357.5; // east

    // Check if point is land (simplified)
    function isLand(lat, lon) {
        // Normalize longitude
        while (lon > 180) lon -= 360;
        while (lon < -180) lon += 360;

        // Very simple land mask for major continents
        // Antarctica
        if (lat < -60) return true;

        // North America
        if (lat > 25 && lat < 70 && lon > -130 && lon < -60) return true;

        // South America
        if (lat > -55 && lat < 12 && lon > -82 && lon < -34) return true;

        // Europe/Africa
        if (lat > -35 && lat < 70 && lon > -15 && lon < 50) return true;

        // Asia
        if (lat > 10 && lat < 70 && lon > 50 && lon < 150) return true;

        // Australia
        if (lat > -45 && lat < -10 && lon > 110 && lon < 155) return true;

        return false;
    }

    // Generate realistic wave patterns
    function generateWaveVelocity(lat, lon) {
        // Skip land
        if (isLand(lat, lon)) {
            return { u: 0, v: 0 };
        }

        let u = 0; // east-west component
        let v = 0; // north-south component

        // Trade winds (15°N to 30°N and 15°S to 30°S) - east to west
        if ((lat > 15 && lat < 30) || (lat > -30 && lat < -15)) {
            u = -3 + Math.sin(lon * Math.PI / 180) * 1.5;
            v = -0.5 + Math.cos(lon * Math.PI / 180) * 0.5;
        }

        // Westerlies (30°N to 60°N and 30°S to 60°S) - west to east
        else if ((lat > 30 && lat < 60) || (lat > -60 && lat < -30)) {
            u = 4 + Math.cos(lon * Math.PI / 180) * 2;
            v = 1 + Math.sin(lon * Math.PI / 180) * 1;
        }

        // Polar regions - weaker, variable
        else if (lat > 60 || lat < -60) {
            u = Math.sin(lon * Math.PI / 90) * 1.5;
            v = -Math.cos(lon * Math.PI / 90) * 1.5;
        }

        // Doldrums (equatorial) - light and variable
        else {
            u = Math.sin(lon * Math.PI / 180) * 1.5;
            v = Math.cos(lon * Math.PI / 180) * 0.8;
        }

        // Add some noise for realism
        u += (Math.random() - 0.5) * 0.5;
        v += (Math.random() - 0.5) * 0.5;

        // Add wave effects based on position
        const waveEffect = Math.sin(lat * Math.PI / 180) * Math.cos(lon * Math.PI / 180);
        u += waveEffect * 0.8;
        v += waveEffect * 0.5;

        return { u, v };
    }

    // Generate data arrays
    const uData = [];
    const vData = [];

    console.log('Generating wave data grid...');

    // Generate grid from north to south, west to east
    for (let y = 0; y < ny; y++) {
        const lat = la1 - (y * dy);

        for (let x = 0; x < nx; x++) {
            const lon = lo1 + (x * dx);

            const velocity = generateWaveVelocity(lat, lon);
            uData.push(velocity.u);
            vData.push(velocity.v);
        }
    }

    console.log(`Generated ${uData.length} grid points (${nx} x ${ny})`);

    // Create the data structure expected by leaflet-velocity
    window.waveData = [
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

    console.log('Wave data ready for leaflet-velocity');
})();
