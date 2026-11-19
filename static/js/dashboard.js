// dashboard.js
// Loads chart data from /api/charts and draws three charts with Chart.js.

applyChartTheme();
const PRIORITY_COLOURS = { Critical: cssColor("--red"), High: cssColor("--orange"), Medium: cssColor("--blue"), Low: cssColor("--gray") };
const STATUS_COLOURS = { "Open": cssColor("--blue"), "In Progress": cssColor("--orange"), "Completed": cssColor("--green"), "Cancelled": cssColor("--gray") };

async function loadCharts() {
    let data;
    try {
        data = await apiRequest("GET", "/api/charts");
    } catch (err) {
        showError(err);
        return;
    }

    // Chart 1: backlog by priority (Phase II View 10)
    new Chart(document.getElementById("backlog-chart"), {
        type: "bar",
        data: {
            labels: data.backlog.map(row => row.priority),
            datasets: [{
                label: "Unfinished work orders",
                data: data.backlog.map(row => row.open_jobs),
                backgroundColor: data.backlog.map(row => PRIORITY_COLOURS[row.priority]),
            }],
        },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
        },
    });

    // Chart 2: all work orders by status
    new Chart(document.getElementById("status-chart"), {
        type: "bar",
        data: {
            labels: data.by_status.map(row => row.status),
            datasets: [{
                label: "Work orders",
                data: data.by_status.map(row => row.total),
                backgroundColor: data.by_status.map(row => STATUS_COLOURS[row.status]),
            }],
        },
        options: {
            indexAxis: "y",     // horizontal bars
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true, ticks: { precision: 0 } } },
        },
    });

    // Chart 3: planned vs. actual outage length (Phase II View 9)
    new Chart(document.getElementById("outage-chart"), {
        type: "bar",
        data: {
            labels: data.outages.map(row => row.label),
            datasets: [
                { label: "Planned days", data: data.outages.map(row => row.planned_days), backgroundColor: cssColor("--fill-strong") },
                { label: "Actual days", data: data.outages.map(row => row.actual_days), backgroundColor: cssColor("--blue") },
            ],
        },
        options: {
            maintainAspectRatio: false,
            scales: { y: { beginAtZero: true, title: { display: true, text: "Days" } } },
        },
    });
}

loadCharts();
