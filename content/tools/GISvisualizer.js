const state = {
    map: null,
    baseLayer: null,
    data: [],
    columns: [],
    markersLayer: null,
    legend: null,
    pointSize: 5,
    opacity: 0.8,
    mapStyle: 'light'
};

const mapStyles = {
    light: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    osm: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
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
    state.map = L.map('map', {
        zoomSnap: 0.25,
        zoomDelta: 0.25,
        wheelPxPerZoomLevel: 120
    }).setView([0, 0], 2);
    setBaseMap(state.mapStyle);

    // Add custom export control
    const ExportControl = L.Control.extend({
        options: { position: 'topleft' },
        onAdd: function (map) {
            const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
            const btn = L.DomUtil.create('a', 'leaflet-control-export', container);
            btn.href = '#';
            btn.title = 'Export Map to PNG';
            btn.style.display = 'flex';
            btn.style.alignItems = 'center';
            btn.style.justifyContent = 'center';
            btn.style.color = '#000';
            btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin: auto;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>`;

            L.DomEvent.disableClickPropagation(container);
            L.DomEvent.on(btn, 'click', function(e) {
                L.DomEvent.preventDefault(e);
                exportMapToPNG();
            });

            return container;
        }
    });
    state.map.addControl(new ExportControl());
}

function exportMapToPNG() {
    log('Generating PNG export...', 'hint');
    const mapEl = document.getElementById('map');
    if (!mapEl) return;
    
    // Use html2canvas to capture map
    html2canvas(mapEl, {
        useCORS: true,
        allowTaint: true,
        backgroundColor: null,
        ignoreElements: (el) => {
            if (!el.classList) return false;
            // Ignore zoom control and our export button
            return el.classList.contains('leaflet-control-zoom') || el.classList.contains('leaflet-control-export');
        }
    }).then(canvas => {
        const link = document.createElement('a');
        link.download = 'gis_export.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
        log('Export complete.', 'success');
    }).catch(err => {
        log('Export failed: ' + err.message, 'error');
    });
}

function setBaseMap(styleKey) {
    if (state.baseLayer) {
        state.map.removeLayer(state.baseLayer);
    }

    let attribution = '';
    if (styleKey === 'light') attribution = '&copy; OpenStreetMap contributors &copy; CARTO';
    else if (styleKey === 'osm') attribution = '&copy; OpenStreetMap contributors';
    else if (styleKey === 'satellite') attribution = 'Tiles &copy; Esri';

    state.baseLayer = L.tileLayer(mapStyles[styleKey], { attribution }).addTo(state.map);
}

function handleCSVUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    log(`Reading file: ${file.name}...`);

    Papa.parse(file, {
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
        complete: function (results) {
            state.data = results.data;
            state.columns = results.meta.fields;

            if (state.data.length === 0) {
                log('CSV is empty or invalid', 'error');
                return;
            }

            log(`Loaded ${state.data.length} rows. Map columns to plot.`, 'success');
            log('Select Latitude and Longitude columns', 'hint');

            populateSelects();
        },
        error: function (error) {
            log(`Error parsing CSV: ${error.message}`, 'error');
        }
    });
}

function populateSelects() {
    const selects = ['col_lat', 'col_lng', 'col_feature'];

    selects.forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        el.innerHTML = '';
        el.disabled = false;

        if (id === 'col_feature') {
            const opt = document.createElement('option');
            opt.value = '';
            opt.innerText = 'None';
            el.appendChild(opt);
        }

        state.columns.forEach(col => {
            const opt = document.createElement('option');
            opt.value = col;
            opt.innerText = col;
            el.appendChild(opt);
        });
    });

    // Auto-guess lat/lng
    const latCol = state.columns.find(c => c && c.toLowerCase().includes('lat'));
    const lngCol = state.columns.find(c => c && (c.toLowerCase().includes('lon') || c.toLowerCase().includes('lng')));

    if (latCol) document.getElementById('col_lat').value = latCol;
    if (lngCol) document.getElementById('col_lng').value = lngCol;

    document.getElementById('btn-plot').disabled = false;
}

function hexToRgb(hex) {
    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

function createIcon(shape, color, radius, opacity) {
    const d = radius * 2;
    let svgHtml = '';
    const sw = 1; // stroke width

    // Base circle for all shapes to retain color and size
    svgHtml = `<circle cx="${radius}" cy="${radius}" r="${Math.max(0, radius - sw)}" fill="${color}" fill-opacity="${opacity}" stroke="#000" stroke-width="${sw}" />`;

    if (shape !== 'circle') {
        let symbol = '';
        if (shape === 'question') symbol = '?';
        else if (shape === 'danger') symbol = '⚠';
        else if (shape === 'alarm') symbol = '⏰';
        else if (shape === 'exclamation') symbol = '!';
        else if (shape === 'toxic') symbol = '☣';

        const fontSize = Math.max(12, radius * 1.5);
        svgHtml += `<text x="${radius}" y="${radius + fontSize * 0.05}" font-size="${fontSize}px" fill="#000" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-weight="bold">${symbol}</text>`;
    }

    return L.divIcon({
        className: 'custom-shape-icon',
        html: `<svg width="${d}" height="${d}" style="overflow: visible;">${svgHtml}</svg>`,
        iconSize: [d, d],
        iconAnchor: [radius, radius],
        popupAnchor: [0, -radius]
    });
}

function getColor(value, min, max, c1, c2) {
    if (value === undefined || value === null || min >= max) return c1 ? c1.hex : '#ff0000';
    
    let ratio = (value - min) / (max - min);
    if (ratio < 0) ratio = 0;
    if (ratio > 1) ratio = 1;
    
    if (!c1 || !c2) {
        // Fallback to blue-red
        const r = Math.floor(255 * ratio);
        const b = Math.floor(255 * (1 - ratio));
        return `rgb(${r}, 0, ${b})`;
    }

    const r = Math.floor(c1.r + (c2.r - c1.r) * ratio);
    const g = Math.floor(c1.g + (c2.g - c1.g) * ratio);
    const b = Math.floor(c1.b + (c2.b - c1.b) * ratio);
    return `rgb(${r}, ${g}, ${b})`;
}

function updateLegend(min, max, featureName, bins) {
    if (state.legend) {
        state.legend.remove();
        state.legend = null;
    }

    if (!featureName || min === Infinity || max === -Infinity || min === max) return;

    const LegendControl = L.Control.extend({
        options: { position: 'bottomright' },
        onAdd: function (map) {
            const div = L.DomUtil.create('div', 'info-legend');

            let legendHtml = `<div class="legend-title">${featureName}</div>`;

            if (bins && bins.length > 0) {
                bins.forEach(bin => {
                    legendHtml += `
                        <div class="legend-scale" style="justify-content: flex-start; gap: 10px; margin-top: 4px;">
                            <div style="width: 15px; height: 15px; background: ${bin.color}; border: 1px solid #000;"></div>
                            <span>[${bin.min}, ${bin.max}]</span>
                        </div>
                    `;
                });
            } else {
                const c1Hex = document.getElementById('color_low').value;
                const c2Hex = document.getElementById('color_high').value;
                legendHtml += `
                    <div class="legend-gradient" style="background-color: ${c1Hex}; background-image: linear-gradient(to right, ${c1Hex}, ${c2Hex});"></div>
                    <div class="legend-scale">
                        <span>${min.toFixed(2)}</span>
                        <span>${max.toFixed(2)}</span>
                    </div>
                `;
            }

            div.innerHTML = legendHtml;

            // Make draggable
            const draggable = new L.Draggable(div);
            draggable.enable();

            // Prevent map interactions when dragging legend
            L.DomEvent.disableClickPropagation(div);
            L.DomEvent.disableScrollPropagation(div);

            div.title = "Click to edit legend properties";
            div.style.cursor = 'pointer';
            L.DomEvent.on(div, 'click', function(e) {
                document.getElementById('legend-modal').style.display = 'block';
            });

            return div;
        }
    });

    state.legend = new LegendControl();
    state.legend.addTo(state.map);
}

function plotData() {
    if (state.markersLayer) {
        state.map.removeLayer(state.markersLayer);
    }

    const latCol = document.getElementById('col_lat').value;
    const lngCol = document.getElementById('col_lng').value;
    const featureCol = document.getElementById('col_feature').value;

    if (!latCol || !lngCol) {
        log('Please select both Latitude and Longitude columns.', 'error');
        return;
    }

    log('Plotting data...');

    let featureMin = Infinity;
    let featureMax = -Infinity;

    if (featureCol) {
        state.data.forEach(row => {
            const val = row[featureCol];
            if (typeof val === 'number') {
                if (val < featureMin) featureMin = val;
                if (val > featureMax) featureMax = val;
            }
        });
    }

    // Apply user overrides
    const userMin = document.getElementById('legend_min').value;
    const userMax = document.getElementById('legend_max').value;
    if (userMin !== '') featureMin = parseFloat(userMin);
    if (userMax !== '') featureMax = parseFloat(userMax);

    const legendTitleInput = document.getElementById('legend_title').value.trim();
    const activeLegendTitle = legendTitleInput !== '' ? legendTitleInput : featureCol;

    const colorLowHex = document.getElementById('color_low').value;
    const colorHighHex = document.getElementById('color_high').value;
    const c1 = hexToRgb(colorLowHex);
    const c2 = hexToRgb(colorHighHex);
    if (c1) c1.hex = colorLowHex;
    if (c2) c2.hex = colorHighHex;

    const markers = [];
    const bounds = [];

    const bins = [];
    document.querySelectorAll('.bin-item').forEach(item => {
        const min = parseFloat(item.querySelector('.bin-min').value);
        const max = parseFloat(item.querySelector('.bin-max').value);
        const color = item.querySelector('.bin-color').value;
        if (!isNaN(min) && !isNaN(max)) {
            bins.push({min, max, color});
        }
    });

    state.data.forEach(row => {
        const lat = row[latCol];
        const lng = row[lngCol];

        if (lat !== undefined && lng !== undefined && lat !== null && lng !== null && typeof lat === 'number' && typeof lng === 'number') {
            let color = '#ff0000'; // default red
            let radius = state.pointSize;

            if (featureCol && typeof row[featureCol] === 'number') {
                const val = row[featureCol];
                
                if (bins.length > 0) {
                    let matched = false;
                    for (let i = 0; i < bins.length; i++) {
                        if (val >= bins[i].min && val <= bins[i].max) {
                            color = bins[i].color;
                            matched = true;
                            break;
                        }
                    }
                    if (!matched) color = '#cccccc'; // Default color for out-of-bounds
                } else {
                    color = getColor(val, featureMin, featureMax, c1, c2);
                }

                if (featureMin !== featureMax) {
                    const minRadius = 2; // Minimum point size
                    // Let the user's selected point_size act as the maximum radius
                    const maxRadius = Math.max(state.pointSize, minRadius + 3);
                    let ratio = (val - featureMin) / (featureMax - featureMin);
                    if (ratio < 0) ratio = 0;
                    if (ratio > 1) ratio = 1;
                    radius = minRadius + (maxRadius - minRadius) * ratio;
                }
            }

            let shape = 'circle';

            const marker = L.marker([lat, lng], {
                icon: createIcon(shape, color, radius, state.opacity)
            });

            marker.customProps = { shape, color, radius };

            // Add popup
            const popupDiv = document.createElement('div');
            popupDiv.style.fontFamily = "'Inter', sans-serif";
            
            let contentHtml = `<b>Location:</b> ${lat.toFixed(4)}, ${lng.toFixed(4)}<br>`;
            if (featureCol) {
                contentHtml += `<b>${featureCol}:</b> ${row[featureCol]}<br>`;
            }
            
            const infoDiv = document.createElement('div');
            infoDiv.innerHTML = contentHtml;
            popupDiv.appendChild(infoDiv);

            const shapeSelectorDiv = document.createElement('div');
            shapeSelectorDiv.style.marginTop = '10px';
            shapeSelectorDiv.style.borderTop = '1px solid #ccc';
            shapeSelectorDiv.style.paddingTop = '8px';
            shapeSelectorDiv.innerHTML = `<label style="display:block; margin-bottom: 4px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase;">Marker Icon</label>`;
            
            const select = document.createElement('select');
            select.style.width = '100%';
            select.style.padding = '4px';
            select.style.fontFamily = "'Inter', sans-serif";
            select.style.fontSize = "0.85rem";
            select.style.border = "1px solid #000";
            
            const shapes = ['circle', 'question', 'danger', 'alarm', 'exclamation', 'toxic'];
            shapes.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s;
                opt.innerText = s.charAt(0).toUpperCase() + s.slice(1);
                if (s === shape) opt.selected = true;
                select.appendChild(opt);
            });

            select.onchange = (e) => {
                const newShape = e.target.value;
                marker.customProps.shape = newShape;
                marker.setIcon(createIcon(newShape, marker.customProps.color, marker.customProps.radius, state.opacity));
            };

            shapeSelectorDiv.appendChild(select);
            popupDiv.appendChild(shapeSelectorDiv);

            marker.bindPopup(popupDiv);

            markers.push(marker);
            bounds.push([lat, lng]);
        }
    });

    if (markers.length > 0) {
        state.markersLayer = L.layerGroup(markers).addTo(state.map);
        state.map.fitBounds(bounds);
        updateLegend(featureMin, featureMax, activeLegendTitle, bins);
        log(`Plotted ${markers.length} points.`, 'success');
        log('Adjust plotting options or explore the map', 'hint');
    } else {
        log('No valid coordinates found.', 'error');
    }
}

function clearMap() {
    if (state.markersLayer) {
        state.map.removeLayer(state.markersLayer);
        state.markersLayer = null;
    }
    if (state.legend) {
        state.legend.remove();
        state.legend = null;
    }
    log('Map cleared.');
}

function addBin() {
    const container = document.getElementById('bins_container');
    const div = document.createElement('div');
    div.className = 'bin-item';
    div.style.display = 'flex';
    div.style.gap = '0.5rem';
    div.style.alignItems = 'center';
    
    div.innerHTML = `
        <input type="number" class="bin-min" placeholder="Min" style="width: 30%; padding: 0.4rem;">
        <input type="number" class="bin-max" placeholder="Max" style="width: 30%; padding: 0.4rem;">
        <input type="color" class="bin-color" value="#ff0000" style="width: 25%; padding: 0; height: 30px; border: 1px solid #000;">
        <button class="btn-remove-bin" style="width: 15%; padding: 0.4rem; background: #ef4444; color: #fff; border: 1px solid #000;">X</button>
    `;
    
    div.querySelector('.btn-remove-bin').onclick = () => {
        div.remove();
        if (state.markersLayer) plotData();
    };
    
    div.querySelectorAll('input').forEach(inp => {
        inp.onchange = () => {
            if (state.markersLayer) plotData();
        };
    });
    
    container.appendChild(div);
}

document.addEventListener('DOMContentLoaded', () => {
    initMap();

    document.getElementById('csv_input').onchange = handleCSVUpload;
    document.getElementById('btn-plot').onclick = plotData;
    document.getElementById('btn-plot').onclick = plotData;
    document.getElementById('btn-clear').onclick = clearMap;
    document.getElementById('btn-add-bin').onclick = addBin;

    ['legend_title', 'legend_min', 'legend_max', 'color_low', 'color_high'].forEach(id => {
        document.getElementById(id).onchange = () => {
            if (state.markersLayer) plotData();
        };
    });
    
    document.getElementById('btn-close-legend-modal').onclick = () => {
        document.getElementById('legend-modal').style.display = 'none';
    };

    document.getElementById('map_style').onchange = (e) => {
        state.mapStyle = e.target.value;
        setBaseMap(state.mapStyle);
    };

    const opacityEl = document.getElementById('opacity');
    opacityEl.oninput = (e) => {
        const val = parseFloat(e.target.value);
        document.getElementById('val-opacity').innerText = val;
        state.opacity = val;
        if (state.markersLayer) {
            plotData();
        }
    };

    const pointSizeSlider = document.getElementById('point_size');
    const pointSizeInput = document.getElementById('val-point-size');

    const updatePointSize = (val) => {
        const parsed = parseFloat(val);
        if (isNaN(parsed) || parsed < 1) return;
        state.pointSize = parsed;
        pointSizeSlider.value = parsed;
        pointSizeInput.value = parsed;
        if (state.markersLayer) {
            plotData();
        }
    };

    pointSizeSlider.oninput = (e) => updatePointSize(e.target.value);
    pointSizeInput.oninput = (e) => updatePointSize(e.target.value);
});
