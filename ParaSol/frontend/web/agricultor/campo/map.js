let map;
let drawnItems;
let drawControl;

const API_BASE_URL = "https://parasol-j08z.onrender.com";

// ─── DATOS HARDCODEADOS (MOCK) ────────────────────────────────────────────────
const MOCK_DATA = {
    rainfall: {
        total_rainfall_mm: 742.5,
        peak_rainfall_mm: 87.3,
        rainy_days: 34
    },
    twi: {
        data: {
            avg_twi: 10.4,
            max_twi: 14.2,
            min_twi: 6.1
        }
    },
    ndvi: {
        ndvi: {
            ndvi_median: 0.28,
            ndvi_mean: 0.31,
            ndvi_min: 0.12,
            ndvi_max: 0.61
        }
    },
    flood: {
        flood_detected: true,
        flooded_area_pct: 18.7,
        flood_days: 12,
        flooded_area_ha: 27.2
    }
};
// ─────────────────────────────────────────────────────────────────────────────

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

    const btn = document.getElementById('btn-analyze');
    const cards = ['card-rainfall', 'card-twi', 'card-ndvi', 'card-flood'];

    btn.innerText = "PROCESANDO...";
    btn.disabled = true;

    // Estados de carga — con optional chaining para evitar null errors
    cards.forEach(id => {
        const lbl = document.getElementById(id)?.querySelector('.status-label');
        if (lbl) {
            lbl.innerText = "CONSULTANDO...";
            lbl.classList.add('animate-pulse');
        }
    });

    // Simular latencia de red (1.2s) antes de mostrar los datos mock
    await new Promise(resolve => setTimeout(resolve, 1200));

    try {
        updateProducerUI(MOCK_DATA.rainfall, MOCK_DATA.twi, MOCK_DATA.ndvi, MOCK_DATA.flood);
    } catch (error) {
        console.error("Error al procesar datos:", error);
        alert("Error al procesar los datos satelitales.");
    } finally {
        btn.innerText = "ANALIZAR MI CAMPO";
        btn.disabled = false;
        cards.forEach(id => {
            const lbl = document.getElementById(id)?.querySelector('.status-label');
            if (lbl) {
                lbl.classList.remove('animate-pulse');
                lbl.innerText = "ONLINE";
            }
        });
    }
}

function updateProducerUI(rainfall, twi, ndvi, flood) {
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
    const setClass = (id, cls) => { const el = document.getElementById(id); if (el) el.className = cls; };

    // 1. Actualizar Métricas
    set('val-rainfall-total', `${rainfall.total_rainfall_mm?.toFixed(1) || '0.0'} mm`);
    set('val-twi-avg', twi.data?.avg_twi?.toFixed(2) || '0.00');
    set('val-ndvi-median', ndvi.ndvi?.ndvi_median?.toFixed(3) || '0.000');
    set('val-flood-pct', `${flood.flooded_area_pct?.toFixed(1) || '0.0'}%`);
    set('val-flood-days', `${flood.flood_days || '0'} DÍAS`);

    // 2. Comparativa Histórica
    const rainDiff = ((rainfall.total_rainfall_mm / 600 - 1) * 100).toFixed(0);
    const ndviDiff = ((ndvi.ndvi?.ndvi_median / 0.5 - 1) * 100).toFixed(0);

    set('val-rainfall-diff', `${rainDiff > 0 ? '+' : ''}${rainDiff}% vs hist.`);
    setClass('val-rainfall-diff', `font-data text-[10px] font-bold ${rainDiff > 20 ? 'text-error' : 'text-secondary'}`);

    set('val-ndvi-diff', `${ndviDiff > 0 ? '+' : ''}${ndviDiff}% vs hist.`);
    setClass('val-ndvi-diff', `font-data text-[10px] font-bold ${ndviDiff < -10 ? 'text-error' : 'text-secondary'}`);

    const compTag = document.getElementById('comparison-tag');
    if (compTag) compTag.innerText = `VS_PROMEDIO_HISTÓRICO: ${ndviDiff < -10 ? 'ANOMALÍA_DETECTADA' : 'NORMAL'}`;

    // Badge de inundación
    const floodBadge = document.getElementById('val-flood-badge');
    if (floodBadge) {
        floodBadge.innerText = flood.flood_detected ? 'INUNDACIÓN' : 'SIN_EVENTO';
        floodBadge.className = `font-data text-[9px] font-bold uppercase ${flood.flood_detected ? 'text-error' : 'text-secondary'}`;
    }

    // TWI status
    const twiVal = twi.data?.avg_twi || 0;
    const twiStatus = document.getElementById('val-twi-status');
    if (twiStatus) {
        twiStatus.innerText = twiVal > 10 ? 'ALTO' : twiVal > 7 ? 'MEDIO' : 'BAJO';
        twiStatus.className = `font-data text-[10px] font-bold uppercase ${twiVal > 10 ? 'text-error' : twiVal > 7 ? 'text-primary' : 'text-secondary'}`;
    }

    // 3. Recomendaciones
    const insights = [];
    if (flood.flood_detected) {
        insights.push({ icon: 'warning', color: 'text-error', title: 'Inundación Detectada', desc: `Se detectó inundación en el ${flood.flooded_area_pct?.toFixed(1)}% del lote (${flood.flood_days} días). Se recomienda evacuar maquinaria y revisar canales de drenaje inmediatamente.` });
    }
    if (twi.data?.avg_twi > 9 && rainfall.total_rainfall_mm > 100) {
        insights.push({ icon: 'water_drop', color: 'text-primary', title: 'Riesgo de Saturación', desc: 'Lote en zona baja con alta acumulación hídrica (TWI ' + twi.data.avg_twi.toFixed(1) + '). Posible asfixia radicular en las próximas 48h.' });
    }
    if (ndvi.ndvi?.ndvi_median < 0.3) {
        insights.push({ icon: 'grass', color: 'text-error', title: 'Vigor Crítico', desc: `NDVI de ${ndvi.ndvi.ndvi_median.toFixed(3)} indica degradación severa del cultivo. Revisar plagas o anegamiento prolongado.` });
    }
    if (rainfall.total_rainfall_mm > 700) {
        insights.push({ icon: 'thunderstorm', color: 'text-primary', title: 'Exceso Hídrico', desc: `Lluvia acumulada de ${rainfall.total_rainfall_mm.toFixed(0)} mm supera el promedio histórico. Evaluar drenaje del lote.` });
    }
    if (insights.length === 0) {
        insights.push({ icon: 'check_circle', color: 'text-secondary', title: 'Estado Óptimo', desc: 'Las métricas satelitales no muestran anomalías críticas en el período analizado.' });
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
    const progress = Math.min((flood.flooded_area_pct / 15) * 100, 100);
    document.getElementById('policy-progress').style.width = `${progress}%`;

    const policyMsg = document.getElementById('policy-message');
    if (flood.flooded_area_pct >= 15) {
        policyMsg.innerText = `UMBRAL DE PAGO ALCANZADO (${flood.flooded_area_pct.toFixed(1)}% > 15%). Payout en proceso de validación on-chain.`;
        policyMsg.className = "p-3 bg-error/10 text-error font-data text-[11px] rounded-lg border border-error/20 alert-pulse";
    } else if (flood.flooded_area_pct > 5) {
        policyMsg.innerText = `ALERTA: Anegamiento al ${flood.flooded_area_pct.toFixed(1)}%. Monitoreando umbral del 15%.`;
        policyMsg.className = "p-3 bg-primary/10 text-primary font-data text-[11px] rounded-lg border border-primary/20";
    } else {
        policyMsg.innerText = "Condiciones normales. Póliza activa sin eventos de pago.";
        policyMsg.className = "p-3 bg-secondary/10 text-secondary font-data text-[11px] rounded-lg border border-secondary/20";
    }
}

window.onload = initMap;