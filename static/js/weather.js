// weather.js
// Outage weather page. Shows saved weather for an outage and lets users
// fetch the current weather from the Open-Meteo API, which the server saves.

const outageSelect = document.getElementById("outage-select");
const fetchButton = document.getElementById("fetch-button");
let weatherChart = null;
applyChartTheme();

async function setupPage() {
    if (canEdit()) fetchButton.classList.remove("hidden");
    try {
        const outages = await apiRequest("GET", "/api/outages");
        fillSelect(outageSelect, outages, "outage_id",
                   o => "Outage " + o.outage_id + ": " + o.station_name + " Unit " + o.unit_number +
                        " (" + o.outage_type + ", " + o.status + ")");
        loadWeather();
    } catch (err) {
        showError(err);
    }
}

async function loadWeather() {
    const outageId = outageSelect.value;
    let data;
    try {
        data = await apiRequest("GET", "/api/outages/" + outageId + "/weather");
    } catch (err) {
        showError(err);
        return;
    }

    // Summary tiles
    const s = data.summary;
    document.getElementById("summary").innerHTML =
        tile(s.readings, "Readings saved") +
        tile(s.avg_temp_c === null ? "-" : s.avg_temp_c + " °C", "Average temperature") +
        tile(s.max_wind_kmh === null ? "-" : s.max_wind_kmh + " km/h", "Highest wind") +
        tile(s.total_precip_mm === null ? "-" : s.total_precip_mm + " mm", "Total precipitation");

    // Table
    const rowsBody = document.getElementById("rows");
    if (data.readings.length === 0) {
        rowsBody.innerHTML = '<tr><td colspan="5" class="empty">No weather saved for this outage yet.</td></tr>';
    } else {
        rowsBody.innerHTML = data.readings.map(r =>
            "<tr><td>" + escapeHtml(r.recorded_at) + "</td><td>" + r.temperature_c + "</td><td>" +
            r.wind_speed_kmh + "</td><td>" + r.precip_mm + "</td><td>" + escapeHtml(r.conditions) + "</td></tr>"
        ).join("");
    }

    drawChart(data.readings);
}

function tile(value, label) {
    return '<div class="stat"><div class="number">' + escapeHtml(value) + '</div><div class="label">' + label + "</div></div>";
}

function drawChart(readings) {
    if (weatherChart) weatherChart.destroy();   // remove the old chart before drawing a new one
    weatherChart = new Chart(document.getElementById("weather-chart"), {
        type: "line",
        data: {
            labels: readings.map(r => r.recorded_at.substring(0, 16)),
            datasets: [
                { label: "Temperature (°C)", data: readings.map(r => r.temperature_c),
                  borderColor: cssColor("--red"), backgroundColor: cssColor("--red"), yAxisID: "y" },
                { label: "Wind (km/h)", data: readings.map(r => r.wind_speed_kmh),
                  borderColor: cssColor("--blue"), backgroundColor: cssColor("--blue"), yAxisID: "y1" },
            ],
        },
        options: {
            maintainAspectRatio: false,
            scales: {
                y: { position: "left", title: { display: true, text: "°C" } },
                y1: { position: "right", title: { display: true, text: "km/h" }, grid: { drawOnChartArea: false } },
            },
        },
    });
}

outageSelect.addEventListener("change", loadWeather);

fetchButton.addEventListener("click", async function () {
    fetchButton.disabled = true;
    fetchButton.textContent = "Contacting weather service...";
    try {
        const result = await apiRequest("POST", "/api/outages/" + outageSelect.value + "/weather");
        const r = result.reading;
        showMessage(result.message + " " + r.conditions + ", " + r.temperature_c + " °C, wind " + r.wind_speed_kmh + " km/h.", "success");
        loadWeather();
    } catch (err) {
        showError(err);
    } finally {
        fetchButton.disabled = false;
        fetchButton.textContent = "Get current weather and save it";
    }
});

setupPage();
