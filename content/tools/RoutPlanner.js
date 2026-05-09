/**
 * Route Pattern Mapper - Stage 1: Network Download
 */

const state = {
    map: null,
    baseNetwork: null,
    cvReady: false,
    originalImg: null, // cv.Mat
    masks: {}, // {color: cv.Mat}
    outlines: {}, // {color: cv.Mat}
    skeletons: {}, // {color: cv.Mat}
    detectedColors: [],
    overlayLayer: null,
    baseNetwork: null,
    streetSegments: [],
    snappedRoutes: {},
    scale: 0.5,
    offsetX: 0.1,
    offsetY: 0.1
};



const COLOR_RANGES = {
    'red': [[0, 100, 20], [10, 255, 255], [160, 100, 20], [180, 255, 255]],
    'orange': [[1, 100, 100], [1, 255, 255]],
    'amber': [[2, 100, 100], [2, 255, 255]],
    'yellow': [[3, 100, 100], [3, 255, 255]],
    'lime': [[4, 100, 100], [4, 255, 255]],
    'chartreuse': [[5, 100, 100], [5, 255, 255]],
    'green': [[6, 100, 100], [6, 255, 255]],
    'blue': [[10, 100, 100], [10, 255, 255]],
    'purple': [[13, 100, 100], [13, 255, 255]],
    'magenta': [[14, 100, 100], [14, 255, 255]]
};

const COLOR_MAP_RGB = {
    'red': [255, 0, 0], 'orange': [255, 165, 0], 'yellow': [255, 255, 0],
    'green': [0, 255, 0], 'blue': [0, 0, 255], 'purple': [128, 0, 128],
    'magenta': [255, 0, 255]
};


function log(msg, type = 'info') {
    const statusLog = document.getElementById('status-log');
    const statusHint = document.getElementById('status-hint');

    if (type === 'hint') {
        if (statusHint) statusHint.innerText = `hint: ${msg}`;
    } else {
        if (statusLog) statusLog.innerText = `>> ${msg}`;
    }
    console.log(`[${type}] ${msg}`);
}

function initMap() {
    state.map = L.map('map').setView([49.2827, -123.1207], 13); // Default Vancouver

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    }).addTo(state.map);
}

async function downloadNetwork() {
    const rawPlaceName = document.getElementById('place_name').value;
    const places = rawPlaceName.split(';').map(p => p.trim()).filter(p => p.length > 0);
    const networkType = document.getElementById('network_type').value;
    const btn = document.getElementById('btn-fetch-map');

    if (places.length === 0) return;

    btn.disabled = true;
    btn.innerText = 'Searching...';
    log(`Downloading ${networkType} network for ${places.join(', ')}`);

    try {
        const geoDataList = [];
        // 1. Geocode locations using Nominatim with 1s delay to respect rate limits
        for (let i = 0; i < places.length; i++) {
            if (i > 0) {
                log(`Waiting 1s to respect Nominatim rate limits...`);
                await new Promise(r => setTimeout(r, 1050));
            }

            const place = places[i];
            const geoData = await new Promise((resolve, reject) => {
                const callbackName = 'nominatimCallback_' + Math.floor(Math.random() * 1000000);
                window[callbackName] = (data) => {
                    delete window[callbackName];
                    document.head.removeChild(script);
                    resolve(data);
                };
                const script = document.createElement('script');
                script.src = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(place)}&json_callback=${callbackName}`;
                script.onerror = () => reject(new Error(`Geocoding failed for ${place}.`));
                document.head.appendChild(script);
            });

            if (!geoData || geoData.length === 0) {
                throw new Error(`Place not found: ${place}`);
            }
            geoDataList.push(geoData[0]);
        }

        log(`Found: ${geoDataList.map(g => g.display_name).join(' AND ')}`, 'success');

        state.map.setView([geoDataList[0].lat, geoDataList[0].lon], 12);

        // 2. Fetch Street Network using Overpass API
        btn.innerText = 'Downloading OSM data...';

        let highwayFilter = '';
        if (networkType === 'bike') highwayFilter = '[highway~"cycleway|path|residential|tertiary|unclassified"]';
        else if (networkType === 'walk') highwayFilter = '[highway~"footway|path|residential|pedestrian"]';
        else highwayFilter = '[highway~"primary|secondary|tertiary|residential|unclassified"]';

        let queryInner = '';
        for (const geo of geoDataList) {
            let areaId = 0;
            // Calculate Overpass Area ID from OSM ID
            if (geo.osm_type === 'relation') areaId = parseInt(geo.osm_id) + 3600000000;
            else if (geo.osm_type === 'way') areaId = parseInt(geo.osm_id) + 2400000000;

            if (areaId > 0) {
                queryInner += `way${highwayFilter}(area:${areaId});\n`;
            } else {
                // Fallback to bounding box
                const bbox = `${geo.boundingbox[0]},${geo.boundingbox[2]},${geo.boundingbox[1]},${geo.boundingbox[3]}`;
                queryInner += `way${highwayFilter}(${bbox});\n`;
            }
        }

        const query = `[out:json][timeout:90];\n(\n${queryInner});\nout body;\n>;\nout skel qt;`;
        const overpassUrl = `https://overpass-api.de/api/interpreter`;

        log('Fetching from Overpass API (this may take a minute for multiple cities)...');

        // Use POST for robust querying
        const osmResponse = await fetch(overpassUrl, {
            method: 'POST',
            body: `data=${encodeURIComponent(query)}`,
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });

        if (!osmResponse.ok) {
            throw new Error('OSM download failed. Overpass API might be busy.');
        }

        const osmData = await osmResponse.json();
        log(`Downloaded ${osmData.elements.length} elements`, 'success');

        // 3. Render Network
        renderNetwork(osmData);

        btn.innerText = 'Download Street Network';
        btn.disabled = false;
        log('Upload a Pattern Image (Step 2) to continue', 'hint');
    } catch (err) {
        log(err.message, 'error');
        btn.innerText = 'Error (Try Again)';
        btn.disabled = false;
    }
}

function renderNetwork(data) {
    if (state.baseNetwork) state.map.removeLayer(state.baseNetwork);

    const nodes = {};
    data.elements.forEach(el => {
        if (el.type === 'node') nodes[el.id] = [el.lat, el.lon];
    });

    state.streetSegments = [];

    const features = data.elements.filter(el => el.type === 'way').map(way => {
        const coords = way.nodes.map(nodeId => [nodes[nodeId][1], nodes[nodeId][0]]);

        // Store segments for snapping [lng, lat] to {lat, lng}
        for (let i = 0; i < coords.length - 1; i++) {
            state.streetSegments.push([
                { lat: coords[i][1], lng: coords[i][0] },
                { lat: coords[i + 1][1], lng: coords[i + 1][0] }
            ]);
        }

        return {
            type: 'Feature',
            geometry: {
                type: 'LineString',
                coordinates: coords
            }
        };
    });

    state.baseNetwork = L.geoJSON(features, {
        style: { color: '#000000', weight: 1, opacity: 0.3 }
    }).addTo(state.map);

    // Fit map to network bounds
    state.map.fitBounds(state.baseNetwork.getBounds());
}

window.initCvApp = function () {
    log('OpenCV.js is ready', 'success');
    state.cvReady = true;
};

// If OpenCV loaded before this script
if (window.cvLoaded && !state.cvReady) {
    window.initCvApp();
}

function handleImageUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
        const img = new Image();
        img.onload = () => {
            const canvas = document.getElementById('canvas_original');
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);
            if (state.cvReady) {
                if (state.originalImg) state.originalImg.delete();
                state.originalImg = cv.imread(canvas);
                state.originalFileName = file.name.split('.').slice(0, -1).join('.') || file.name;
                document.getElementById('btn-process-image').disabled = false;
                log(`Image loaded: ${file.name}`);
                log('Click Pattern Image button to process', 'hint');
            } else {
                log('Warning: OpenCV is still loading. Please try selecting the image again in a few seconds.', 'error');
            }
        };
        img.src = event.target.result;
    };
    reader.readAsDataURL(file);
}



async function processImage() {
    if (!state.originalImg || !state.cvReady) return;

    log('Processing image (Stage 2: Color Detection)...');

    const hsv = new cv.Mat();
    cv.cvtColor(state.originalImg, hsv, cv.COLOR_RGBA2RGB);
    cv.cvtColor(hsv, hsv, cv.COLOR_RGB2HSV);

    const totalPixels = hsv.rows * hsv.cols;
    const minPixelsThreshold = totalPixels * 0.001;

    state.detectedColors = [];
    // Clear old masks
    Object.values(state.masks).forEach(m => m.delete());
    state.masks = {};

    for (const [color, ranges] of Object.entries(COLOR_RANGES)) {
        let mask = new cv.Mat();
        if (color === 'red') {
            const low1 = new cv.Mat(hsv.rows, hsv.cols, hsv.type(), [ranges[0][0], ranges[0][1], ranges[0][2], 0]);
            const high1 = new cv.Mat(hsv.rows, hsv.cols, hsv.type(), [ranges[1][0], ranges[1][1], ranges[1][2], 255]);
            const low2 = new cv.Mat(hsv.rows, hsv.cols, hsv.type(), [ranges[2][0], ranges[2][1], ranges[2][2], 0]);
            const high2 = new cv.Mat(hsv.rows, hsv.cols, hsv.type(), [ranges[3][0], ranges[3][1], ranges[3][2], 255]);

            let m1 = new cv.Mat();
            let m2 = new cv.Mat();
            cv.inRange(hsv, low1, high1, m1);
            cv.inRange(hsv, low2, high2, m2);
            cv.add(m1, m2, mask);

            low1.delete(); high1.delete(); low2.delete(); high2.delete();
            m1.delete(); m2.delete();
        } else {
            const low = new cv.Mat(hsv.rows, hsv.cols, hsv.type(), [ranges[0][0], ranges[0][1], ranges[0][2], 0]);
            const high = new cv.Mat(hsv.rows, hsv.cols, hsv.type(), [ranges[1][0], ranges[1][1], ranges[1][2], 255]);
            cv.inRange(hsv, low, high, mask);
            low.delete(); high.delete();
        }

        const pixelCount = cv.countNonZero(mask);
        if (pixelCount > minPixelsThreshold) {
            state.detectedColors.push(color);
            state.masks[color] = mask.clone();
        }
        mask.delete();
    }

    hsv.delete();
    log(`Detected colors: ${state.detectedColors.join(', ')}`, 'success');

    // Stage 3: Boundary Extraction
    extractBoundaries();

    renderResults();
}

function extractBoundaries() {
    log('Extracting boundaries (Stage 3)...');

    // Clear old data
    Object.values(state.outlines).forEach(m => m.delete());
    Object.values(state.skeletons).forEach(m => m.delete());
    state.outlines = {};
    state.skeletons = {};

    const kernel3 = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(3, 3));
    const kernel2 = cv.getStructuringElement(cv.MORPH_RECT, new cv.Size(2, 2));

    for (const color of state.detectedColors) {
        const mask = state.masks[color];

        // 1. Clean mask
        let cleaned = new cv.Mat();
        cv.morphologyEx(mask, cleaned, cv.MORPH_CLOSE, kernel3);
        cv.morphologyEx(cleaned, cleaned, cv.MORPH_OPEN, kernel3);

        // 2. Find contours
        let contours = new cv.MatVector();
        let hierarchy = new cv.Mat();
        cv.findContours(cleaned, contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE);

        if (contours.size() > 0) {
            // Find largest contour
            let largestIdx = 0;
            let maxArea = 0;
            for (let i = 0; i < contours.size(); i++) {
                const area = cv.contourArea(contours.get(i));
                if (area > maxArea) {
                    maxArea = area;
                    largestIdx = i;
                }
            }

            // 3. Create outline
            let outline = cv.Mat.zeros(mask.rows, mask.cols, cv.CV_8UC1);
            cv.drawContours(outline, contours, largestIdx, new cv.Scalar(255), 1);
            state.outlines[color] = outline;

            // 4. Create "skeleton" (morpological closure of outline as per script)
            let skeleton = new cv.Mat();
            cv.morphologyEx(outline, skeleton, cv.MORPH_CLOSE, kernel2);
            state.skeletons[color] = skeleton;
        }

        cleaned.delete(); contours.delete(); hierarchy.delete();
    }

    kernel3.delete(); kernel2.delete();

    renderResults();
    updateAnchorSelect();
    updateOverlay();
    document.getElementById('btn-snap-route').disabled = false;
    document.getElementById('btn-export-gpx').disabled = false;
    log('Adjust Overlay settings (Step 3) or proceed to Match & Export (Step 4)', 'hint');
}

function renderResults() {
    if (state.detectedColors.length === 0) return;

    const combinedRoutes = cv.Mat.zeros(state.originalImg.rows, state.originalImg.cols, cv.CV_8UC4);

    for (const color of state.detectedColors) {
        const skeleton = state.skeletons[color];
        if (!skeleton) continue;

        const rgb = COLOR_MAP_RGB[color] || [255, 0, 0];

        for (let y = 0; y < skeleton.rows; y++) {
            for (let x = 0; x < skeleton.cols; x++) {
                if (skeleton.ucharPtr(y, x)[0] > 0) {
                    const idx = (y * skeleton.cols + x) * 4;
                    combinedRoutes.data[idx] = rgb[0];
                    combinedRoutes.data[idx + 1] = rgb[1];
                    combinedRoutes.data[idx + 2] = rgb[2];
                    combinedRoutes.data[idx + 3] = 255;
                }
            }
        }
    }

    cv.imshow('canvas_mask', combinedRoutes);
    combinedRoutes.delete();
}


function updateAnchorSelect() {
    const select = document.getElementById('anchor_color');
    select.innerHTML = '';
    state.detectedColors.forEach(color => {
        const opt = document.createElement('option');
        opt.value = color;
        opt.innerText = color;
        select.appendChild(opt);
    });
}

function updateOverlay() {
    if (!state.originalImg || state.detectedColors.length === 0) return;

    // Clear any snapped routes since the overlay is moving
    if (state.snappedLayers) {
        state.snappedLayers.forEach(layer => state.map.removeLayer(layer));
        state.snappedLayers = [];
    }
    state.snappedRoutes = {};

    if (state.overlayLayer) state.map.removeLayer(state.overlayLayer);
    if (state.detectedColors.length === 0) return;

    const bounds = state.map.getBounds();
    const width = bounds.getEast() - bounds.getWest();
    const height = bounds.getNorth() - bounds.getSouth();

    const anchorColor = document.getElementById('anchor_color').value || state.detectedColors[0];
    const anchorSkeleton = state.skeletons[anchorColor];
    if (!anchorSkeleton) return;

    const imgWidth = anchorSkeleton.cols;
    const imgHeight = anchorSkeleton.rows;

    const routeWidth = width * state.scale;
    const routeHeight = height * state.scale;

    const routeRight = bounds.getEast() - (width * state.offsetX);
    const routeBottom = bounds.getSouth() + (height * state.offsetY);
    const routeLeft = routeRight - routeWidth;
    const routeTop = routeBottom + routeHeight;

    const overlayBounds = [[routeBottom, routeLeft], [routeTop, routeRight]];

    // Create combined transparent image for overlay
    const canvas = document.createElement('canvas');
    canvas.width = imgWidth;
    canvas.height = imgHeight;
    const ctx = canvas.getContext('2d');

    for (const color of state.detectedColors) {
        const skeleton = state.skeletons[color];
        const rgb = COLOR_MAP_RGB[color] || [255, 0, 0];
        ctx.fillStyle = `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.8)`;

        for (let y = 0; y < skeleton.rows; y++) {
            for (let x = 0; x < skeleton.cols; x++) {
                if (skeleton.ucharPtr(y, x)[0] > 0) {
                    ctx.fillRect(x, y, 2, 2);
                }
            }
        }
    }

    state.overlayLayer = L.imageOverlay(canvas.toDataURL(), overlayBounds, { opacity: 0.8 }).addTo(state.map);
}

function generateCoordinates() {
    log('Generating GPX coordinates (Nearest-Neighbor)...');

    const generated = {};
    const bounds = state.overlayLayer.getBounds();
    const west = bounds.getWest();
    const east = bounds.getEast();
    const south = bounds.getSouth();
    const north = bounds.getNorth();

    for (const color of state.detectedColors) {
        const skeleton = state.skeletons[color];
        const pixels = [];
        for (let y = 0; y < skeleton.rows; y++) {
            for (let x = 0; x < skeleton.cols; x++) {
                if (skeleton.ucharPtr(y, x)[0] > 0) pixels.push({ x, y });
            }
        }

        if (pixels.length === 0) continue;

        // Stage 7: Nearest Neighbor Ordering
        let ordered = [];
        let remaining = [...pixels];
        let current = remaining.splice(0, 1)[0];
        ordered.push(current);

        while (remaining.length > 0) {
            let minDist = Infinity;
            let minIdx = -1;
            for (let i = 0; i < remaining.length; i++) {
                const d = Math.pow(current.x - remaining[i].x, 2) + Math.pow(current.y - remaining[i].y, 2);
                if (d < minDist) {
                    minDist = d;
                    minIdx = i;
                }
            }
            current = remaining.splice(minIdx, 1)[0];
            ordered.push(current);
        }

        // Convert to LatLng
        const coords = ordered.map(p => {
            const lat = north - (p.y / skeleton.rows) * (north - south);
            const lng = west + (p.x / skeleton.cols) * (east - west);
            return { lat, lng };
        });

        generated[color] = coords;
    }
    return generated;
}

function closestPointOnSegment(p, v, w) {
    const l2 = Math.pow(v.lng - w.lng, 2) + Math.pow(v.lat - w.lat, 2);
    if (l2 === 0) return v;
    let t = ((p.lng - v.lng) * (w.lng - v.lng) + (p.lat - v.lat) * (w.lat - v.lat)) / l2;
    t = Math.max(0, Math.min(1, t));
    return {
        lat: v.lat + t * (w.lat - v.lat),
        lng: v.lng + t * (w.lng - v.lng)
    };
}

function dist2(p, w) {
    return Math.pow(p.lng - w.lng, 2) + Math.pow(p.lat - w.lat, 2);
}

function snapToNetwork() {
    if (!state.overlayLayer || state.streetSegments.length === 0) return;

    log('Snapping routes to map network (this may take a few seconds)...');

    const theoreticalRoutes = generateCoordinates();
    state.snappedRoutes = {};

    // Clear any previous snapped polylines
    if (state.snappedLayers) {
        state.snappedLayers.forEach(layer => state.map.removeLayer(layer));
    }
    state.snappedLayers = [];

    for (const color of Object.keys(theoreticalRoutes)) {
        const coords = theoreticalRoutes[color];
        const snapped = [];

        for (const p of coords) {
            let minDist = Infinity;
            let bestPoint = null;

            for (const seg of state.streetSegments) {
                const proj = closestPointOnSegment(p, seg[0], seg[1]);
                const d = dist2(p, proj);
                if (d < minDist) {
                    minDist = d;
                    bestPoint = proj;
                }
            }
            if (bestPoint) snapped.push(bestPoint);
        }

        state.snappedRoutes[color] = snapped;

        // Visualize snapped route
        const rgb = COLOR_MAP_RGB[color] || [255, 255, 255];
        const hex = "#" + rgb.map(x => x.toString(16).padStart(2, '0')).join('');

        const layer = L.polyline(snapped.map(p => [p.lat, p.lng]), {
            color: hex,
            weight: 3,
            opacity: 0.8
        }).addTo(state.map);

        state.snappedLayers.push(layer);
    }

    log('Snapping complete!', 'success');
}

async function exportGPX() {
    if (state.detectedColors.length === 0) return;

    let routesToExport = state.snappedRoutes;
    if (Object.keys(routesToExport).length === 0) {
        routesToExport = generateCoordinates();
    }

    for (const color of state.detectedColors) {
        const coords = routesToExport[color];
        if (!coords || coords.length === 0) continue;

        // Stage 9: Export GPX
        await saveGPX(color, coords);
    }
}

async function saveGPX(color, coords) {
    let gpx = `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="RoutePatternMapper" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>${color} route</name>
    <trkseg>`;

    coords.forEach(c => {
        gpx += `\n      <trkpt lat="${c.lat.toFixed(6)}" lon="${c.lng.toFixed(6)}"></trkpt>`;
    });

    gpx += `\n    </trkseg>
  </trk>
</gpx>`;

    const now = new Date();
    const timestamp = now.getFullYear() + '-' +
        String(now.getMonth() + 1).padStart(2, '0') + '-' +
        String(now.getDate()).padStart(2, '0') + '_' +
        String(now.getHours()).padStart(2, '0') + '-' +
        String(now.getMinutes()).padStart(2, '0') + '-' +
        String(now.getSeconds()).padStart(2, '0');

    const baseName = state.originalFileName || 'route';
    const filename = `${baseName}_${color}_${timestamp}.gpx`;

    try {
        if ('showSaveFilePicker' in window) {
            const handle = await window.showSaveFilePicker({
                suggestedName: filename,
                types: [{
                    description: 'GPX File',
                    accept: { 'application/gpx+xml': ['.gpx'] },
                }],
            });
            const writable = await handle.createWritable();
            await writable.write(gpx);
            await writable.close();
            log(`GPX route for color ${color} saved to: ${handle.name}`, 'success');
        } else {
            // Fallback for older browsers
            const blob = new Blob([gpx], { type: 'application/gpx+xml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a); // Required for Chrome/Firefox to respect the filename
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            log(`GPX route for color ${color} downloaded: ${filename}`, 'success');
        }
    } catch (err) {
        if (err.name !== 'AbortError') {
            log(`Failed to save GPX: ${err.message}`, 'error');
        }
    }
}

function renderResults() {
    renderMasks();
    renderRoutes();
}

function renderMasks() {
    // ... just ensuring it's called
}

function renderRoutes() {
    if (state.detectedColors.length === 0) return;

    const combinedRoutes = cv.Mat.zeros(state.originalImg.rows, state.originalImg.cols, cv.CV_8UC4);

    for (const color of state.detectedColors) {
        const skeleton = state.skeletons[color];
        if (!skeleton) continue;

        const rgb = COLOR_MAP_RGB[color] || [255, 0, 0];

        for (let y = 0; y < skeleton.rows; y++) {
            for (let x = 0; x < skeleton.cols; x++) {
                if (skeleton.ucharPtr(y, x)[0] > 0) {
                    const idx = (y * skeleton.cols + x) * 4;
                    combinedRoutes.data[idx] = rgb[0];
                    combinedRoutes.data[idx + 1] = rgb[1];
                    combinedRoutes.data[idx + 2] = rgb[2];
                    combinedRoutes.data[idx + 3] = 255;
                }
            }
        }
    }

    cv.imshow('canvas_mask', combinedRoutes); // Reusing canvas_mask for simplicity or could add another
    combinedRoutes.delete();
}


document.addEventListener('DOMContentLoaded', () => {
    initMap();
    document.getElementById('btn-fetch-map').onclick = downloadNetwork;
    document.getElementById('image_input').onchange = handleImageUpload;
    document.getElementById('btn-process-image').onclick = processImage;
    document.getElementById('btn-snap-route').onclick = snapToNetwork;
    document.getElementById('btn-export-gpx').onclick = exportGPX;

    ['scale', 'offset_x', 'offset_y'].forEach(id => {
        const el = document.getElementById(id);
        el.oninput = (e) => {
            const val = parseFloat(e.target.value);
            document.getElementById(`val-${id.replace('_', '-')}`).innerText = val.toFixed(2);
            state[id === 'scale' ? 'scale' : id === 'offset_x' ? 'offsetX' : 'offsetY'] = val;
            updateOverlay();
        };
    });

    document.getElementById('anchor_color').onchange = updateOverlay;
});
