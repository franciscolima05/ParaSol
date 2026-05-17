let map;
let drawnItems;
let drawControl;

const API_BASE_URL = "https://parasol-j08z.onrender.com";

function initMap() {
    map = L.map('map', {
        zoomControl: false,
        attributionControl: false
    }).setView([-38.2, -60.3], 13);

    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19
    }).addTo(map);

    drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);

    const drawOptions = {
        edit: { featureGroup: drawnItems, poly: { allowIntersection: false } },
        draw: {
            polygon: { allowIntersection: false, showArea: true, shapeOptions: { color: '#785a00', fillOpacity: 0.3 } },
            rectangle: { shapeOptions: { color: '#785a00', fillOpacity: 0.3 } },
            polyline: false, circle: false, marker: false, circlemarker: false
        }
    };

    drawControl = new L.Control.Draw(drawOptions);
    map.addControl(drawControl);

    map.on(L.Draw.Event.CREATED, function (event) {
        const layer = event.layer;
        drawnItems.clearLayers();
        drawnItems.addLayer(layer);
        updateArea(layer);
        exportGeoJSON();
        document.querySelectorAll('#results-container > div').forEach(el => el.classList.remove('opacity-50'));
    });

    map.on(L.Draw.Event.DELETED, function () { resetUI(); });

    map.on('move', function() {
        const center = map.getCenter();
        document.getElementById('lat-display').textContent = center.lat.toFixed(3);
        document.getElementById('lng-display').textContent = center.lng.toFixed(3);
    });
}

function resetUI() {
    document.getElementById("area-display").innerText = "0.00 ha";
    document.getElementById("geojson-input").value = "";
    document.querySelectorAll('#results-container > div').forEach(el => el.classList.add('opacity-50'));
    document.getElementById('comparison-tag').innerText = "VS_PROMEDIO_HISTÓRICO: ---";
    document.getElementById('policy-progress').style.width = "0%";
    document.getElementById('insights-container').innerHTML = '<div class="p-3 bg-surface-container-high rounded-xl border border-outline-variant"><div class="font-data text-[11px] text-on-surface-variant">Selecciona un lote para generar recomendaciones.</div></div>';
}

function updateArea(layer) {
    const geojson = layer.toGeoJSON();
    const area = turf.area(geojson);
    const hectares = (area / 10000).toFixed(2);
    document.getElementById("area-display").innerText = `${hectares} ha`;
}

function startDrawPolygon() { new L.Draw.Polygon(map, drawControl.options.draw.polygon).enable(); }
function clearMap() { resetUI(); drawnItems.clearLayers(); }

function exportGeoJSON() {
    if (drawnItems.getLayers().length === 0) return;
    const geojson = drawnItems.toGeoJSON();
    const payload = { polygon: geojson.features[0].geometry };
    document.getElementById("geojson-input").value = JSON.stringify(payload);
}

async function analyzeField() {
    const geojsonRaw = document.getElementById('geojson-input').value;
    if (!geojsonRaw) { alert("ERROR: Dibuja una parcela primero."); return; }

    let geojsonData = JSON.parse(geojsonRaw);
    const startDate = document.getElementById('date-start').value;
    const endDate = document.getElementById('date-end').value;
    const btn = document.getElementById('btn-analyze');
    
    btn.innerText = "PROCESANDO...";
    btn.disabled = true;

    // Loading states
    const cards = ['card-rainfall', 'card-twi', 'card-ndvi', 'card-flood'];
    cards.forEach(id => {
        const card = document.getElementById(id);
        card.querySelector('.status-label').innerText = "CONSULTANDO...";
        card.querySelector('.status-label').classList.add('animate-pulse');
    });

    try {
        const [rainfallRes, twiRes, ndviRes, floodRes] = await Promise.all([
            fetch(`${API_BASE_URL}/rainfall/check`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ coordinates: geojsonData.polygon.coordinates, start_date: startDate, end_date: endDate })
            }),
            fetch(`${API_BASE_URL}/analysis/twi`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ polygon: geojsonData.polygon })
            }),
            fetch(`${API_BASE_URL}/analysis/ndvi`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ polygon: geojsonData.polygon })
            }),
            fetch(`${API_BASE_URL}/analysis/flood`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    polygon: geojsonData.polygon,
                    pre_event: { start_date: "2024-01-01", end_date: "2024-01-31" },
                    post_event: { start_date: startDate, end_date: endDate }
                })
            })
        ]);

        const rainfall = await rainfallRes.json();
        const twi = await twiRes.json();
        const ndvi = await ndviRes.json();
        const flood = await floodRes.json();

        updateProducerUI(rainfall, twi, ndvi, flood);

    } catch (error) {
        console.error("API Error:", error);
        alert("Error de conexión con el motor satelital.");
    } finally {
        btn.innerText = "ANALIZAR MI CAMPO";
        btn.disabled = false;
        cards.forEach(id => document.getElementById(id).querySelector('.status-label').classList.remove('animate-pulse'));
    }
}

function updateProducerUI(rainfall, twi, ndvi, flood) {
    // 1. Actualizar Métricas
    document.getElementById('val-rainfall-total').innerText = `${rainfall.total_rainfall_mm?.toFixed(1) || '0.0'} mm`;
    document.getElementById('val-twi-avg').innerText = twi.data?.avg_twi?.toFixed(2) || '0.00';
    document.getElementById('val-ndvi-median').innerText = ndvi.ndvi?.ndvi_median?.toFixed(3) || '0.000';
    document.getElementById('val-flood-pct').innerText = `${flood.flooded_area_pct?.toFixed(1) || '0.0'}%`;
    document.getElementById('val-flood-days').innerText = `${flood.flood_days || '0'} DÍAS`;

    // 2. Simular Comparativa Histórica (Lógica de negocio frontend)
    const rainDiff = ((rainfall.total_rainfall_mm / 600 - 1) * 100).toFixed(0); // Base 600mm
    const ndviDiff = ((ndvi.ndvi?.ndvi_median / 0.5 - 1) * 100).toFixed(0); // Base 0.5
    
    document.getElementById('val-rainfall-diff').innerText = `${rainDiff > 0 ? '+' : ''}${rainDiff}% vs hist.`;
    document.getElementById('val-rainfall-diff').className = `font-data text-[10px] font-bold ${rainDiff > 20 ? 'text-error' : 'text-secondary'}`;
    
    document.getElementById('val-ndvi-diff').innerText = `${ndviDiff > 0 ? '+' : ''}${ndviDiff}% vs hist.`;
    document.getElementById('val-ndvi-diff').className = `font-data text-[10px] font-bold ${ndviDiff < -10 ? 'text-error' : 'text-secondary'}`;

    document.getElementById('comparison-tag').innerText = `VS_PROMEDIO_HISTÓRICO: ${ndviDiff < -10 ? 'ANOMALÍA_DETECTADA' : 'NORMAL'}`;

    // 3. Generar Recomendaciones (Insights)
    const insights = [];
    if (flood.flood_detected) {
        insights.push({ icon: 'warning', color: 'text-error', title: 'Inundación Detectada', desc: 'Se recomienda evacuar maquinaria y revisar canales de drenaje inmediatamente.' });
    }
    if (twi.data?.avg_twi > 9 && rainfall.total_rainfall_mm > 100) {
        insights.push({ icon: 'water_drop', color: 'text-primary', title: 'Riesgo de Saturación', desc: 'Lote en zona baja con alta acumulación hídrica. Posible asfixia radicular.' });
    }
    if (ndvi.ndvi?.ndvi_median < 0.3) {
        insights.push({ icon: 'Grass', color: 'text-error', title: 'Vigor Crítico', desc: 'El cultivo muestra signos de degradación severa. Revisar plagas o anegamiento.' });
    }
    if (insights.length === 0) {
        insights.push({ icon: 'check_circle', color: 'text-secondary', title: 'Estado Óptimo', desc: 'Las métricas satelitales no muestran anomalías críticas en el período.' });
    }

    const insightsContainer = document.getElementById('insights-container');
    insightsContainer.innerHTML = insights.map(item => `
        <div class="p-3 bg-surface-container-high rounded-xl border border-outline-variant flex gap-3">
            <span class="material-symbols-outlined ${item.color} text-[20px]">${item.icon}</span>
            <div>
                <div class="font-data text-[12px] font-bold text-on-surface uppercase">${item.title}</div>
                <div class="font-body text-[11px] text-on-surface-variant">${item.desc}</div>
            </div>
        </div>
    `).join('');

    // 4. Estado de Póliza
    const progress = Math.min((flood.flooded_area_pct / 15) * 100, 100); // Umbral 15%
    document.getElementById('policy-progress').style.width = `${progress}%`;
    
    const policyMsg = document.getElementById('policy-message');
    if (flood.flooded_area_pct >= 15) {
        policyMsg.innerText = "UMBRAL DE PAGO ALCANZADO. Payout en proceso de validación on-chain.";
        policyMsg.className = "p-3 bg-error/10 text-error font-data text-[11px] rounded-lg border border-error/20 alert-pulse";
    } else if (flood.flooded_area_pct > 5) {
        policyMsg.innerText = "ALERTA: Anegamiento parcial detectado. Monitoreando umbral del 15%.";
        policyMsg.className = "p-3 bg-primary/10 text-primary font-data text-[11px] rounded-lg border border-primary/20";
    } else {
        policyMsg.innerText = "Condiciones normales. Póliza activa sin eventos de pago.";
        policyMsg.className = "p-3 bg-secondary/10 text-secondary font-data text-[11px] rounded-lg border border-secondary/20";
    }
}

window.onload = initMap;
