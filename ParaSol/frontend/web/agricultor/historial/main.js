const MOCK_HISTORY = [
    { id: 1, timestamp: "15 MAY 2024", period: "MAR-MAY", area: "145.2", rainfall: "412", ndvi: "0.74", floodDetected: true, floodPct: "18" },
    { id: 2, timestamp: "02 ABR 2024", period: "MAR-ABR", area: "145.2", rainfall: "125", ndvi: "0.68", floodDetected: false, floodPct: "2" }
];

function renderHistory() {
    const tbody = document.getElementById('history-table-body');

    tbody.innerHTML = MOCK_HISTORY.map(e => `
        <tr>
            <td class="p-6">${e.timestamp}</td>
            <td class="p-6">${e.period}</td>
            <td class="p-6 text-center">${e.area}</td>
            <td class="p-6 text-center">${e.rainfall}</td>
            <td class="p-6 text-center">${e.ndvi}</td>
            <td class="p-6">
                ${e.floodDetected ? 'FLOOD' : 'OK'}
            </td>
            <td class="p-6 text-right">
                <button onclick="reloadAnalysis(${e.id})">Recargar</button>
            </td>
        </tr>
    `).join('');
}

function reloadAnalysis(id) {
    console.log(id);
}

function clearHistory() {
    MOCK_HISTORY.length = 0;
    renderHistory();
}

window.onload = renderHistory;
