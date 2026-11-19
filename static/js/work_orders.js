// work_orders.js
// Work orders page: search/filter, list, create, edit and delete,
// all done with fetch() so the page never reloads.

const filterForm = document.getElementById("filter-form");
const rowsBody = document.getElementById("work-order-rows");
const formCard = document.getElementById("form-card");
const form = document.getElementById("work-order-form");

// Common job titles shown as suggestions while typing
const TITLE_SUGGESTIONS = [
    "Replace pump seal", "Replace valve packing", "Calibrate pressure sensor",
    "Calibrate temperature sensor", "Vibration analysis", "Lubricate bearings",
    "Clean heat exchanger tubes", "Repair pipe leak", "Pipe wall thickness check",
    "Overhaul motor", "Inspect motor wiring", "Rebuild valve actuator",
];

// ---------------------------------------------------------------
// Page setup
// ---------------------------------------------------------------

async function setupPage() {
    document.getElementById("title-suggestions").innerHTML =
        TITLE_SUGGESTIONS.map(t => '<option value="' + t + '">').join("");

    if (canEdit()) {
        document.getElementById("new-button").classList.remove("hidden");
    }

    try {
        const stations = await apiRequest("GET", "/api/stations");
        fillSelect(document.getElementById("f-station"), stations, "station_id", s => s.name, "Any");

        const equipment = await apiRequest("GET", "/api/equipment");
        fillSelect(document.getElementById("equipment_id"), equipment, "equipment_id",
                   e => e.tag_number + " - " + e.name, "Choose equipment...");
    } catch (err) {
        showError(err);
    }

    loadWorkOrders();
}

// ---------------------------------------------------------------
// List with search and filters
// ---------------------------------------------------------------

async function loadWorkOrders() {
    // Turn the filter form into a query string, e.g. ?status=Open&priority=High
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(formToObject(filterForm))) {
        if (value !== "") params.append(key, value);
    }

    let workOrders;
    try {
        workOrders = await apiRequest("GET", "/api/work_orders?" + params.toString());
    } catch (err) {
        showError(err);
        return;
    }

    document.getElementById("result-count").textContent = workOrders.length + " work order(s) found";

    if (workOrders.length === 0) {
        rowsBody.innerHTML = '<tr><td colspan="9" class="empty">No work orders match these filters.</td></tr>';
        return;
    }

    const todayDate = today();
    rowsBody.innerHTML = workOrders.map(wo => {
        const isOverdue = wo.due_date < todayDate && (wo.status === "Open" || wo.status === "In Progress");
        let buttons = "";
        if (canEdit()) buttons += '<button class="small secondary" onclick="editWorkOrder(' + wo.work_order_id + ')">Edit</button> ';
        if (isAdmin()) buttons += '<button class="small danger" onclick="deleteWorkOrder(' + wo.work_order_id + ')">Delete</button>';

        return "<tr>" +
            "<td>" + wo.work_order_id + "</td>" +
            "<td>" + escapeHtml(wo.title) + "</td>" +
            "<td>" + escapeHtml(wo.tag_number) + "</td>" +
            "<td>" + escapeHtml(wo.station_name) + " U" + wo.unit_number + "</td>" +
            "<td>" + tag(wo.priority) + "</td>" +
            "<td>" + tag(wo.status) + "</td>" +
            '<td class="' + (isOverdue ? "overdue" : "") + '">' + wo.due_date + (isOverdue ? " (overdue)" : "") + "</td>" +
            "<td>" + show(wo.worker_name) + "</td>" +
            "<td>" + buttons + "</td>" +
            "</tr>";
    }).join("");
}

filterForm.addEventListener("submit", function (event) {
    event.preventDefault();
    loadWorkOrders();
});

// Filters update the list straight away when a dropdown or date changes
filterForm.querySelectorAll("select, input[type=date]").forEach(el => el.addEventListener("change", loadWorkOrders));

document.getElementById("clear-filters").addEventListener("click", function () {
    filterForm.reset();
    loadWorkOrders();
});

// ---------------------------------------------------------------
// Auto-fill: when equipment is chosen, show its location and fill the
// outage and worker dropdowns with matching choices
// ---------------------------------------------------------------

function keepOption(select, value, label) {
    const found = Array.from(select.options).some(opt => opt.value === String(value));
    if (!found) {
        select.insertAdjacentHTML("beforeend", '<option value="' + escapeHtml(value) + '">' + escapeHtml(label) + "</option>");
    }
    select.value = value;
}

async function loadEquipmentDetails(equipmentId, selectedOutage, selectedWorker, selectedWorkerName) {
    const info = document.getElementById("location-info");
    const outageSelect = document.getElementById("outage_id");
    const workerSelect = document.getElementById("worker_id");

    if (!equipmentId) {
        info.textContent = "Choose equipment to see where it is.";
        fillSelect(outageSelect, [], "outage_id", o => "", "Not part of an outage");
        fillSelect(workerSelect, [], "worker_id", w => "", "Unassigned");
        return;
    }

    try {
        const eq = await apiRequest("GET", "/api/equipment/" + equipmentId);
        info.textContent = eq.station_name + " Unit " + eq.unit_number + "  |  " + eq.system_name +
                           "  |  " + eq.equipment_type + ", inspected every " + eq.inspection_interval_days + " days";

        fillSelect(outageSelect, eq.outages, "outage_id",
                   o => "Outage " + o.outage_id + " (" + o.outage_type + ", " + o.status + ")", "Not part of an outage");
        fillSelect(workerSelect, eq.workers, "worker_id",
                   w => w.fname + " " + w.lname + " (" + w.trade + ")", "Unassigned");

        // When editing, keep the values the work order already had.
        // If the old value is no longer in the list (for example the outage is completed
        // or the worker's certification expired), add it so it is not lost on save.
        if (selectedOutage) {
            keepOption(outageSelect, selectedOutage, "Outage " + selectedOutage + " (current)");
        }
        if (selectedWorker) {
            keepOption(workerSelect, selectedWorker, (selectedWorkerName || "Worker " + selectedWorker) + " (current)");
        }
    } catch (err) {
        showError(err);
    }
}

document.getElementById("equipment_id").addEventListener("change", function () {
    loadEquipmentDetails(this.value);
});

// Fill in today's date as the completed date when status changes to Completed
document.getElementById("status").addEventListener("change", function () {
    const completed = document.getElementById("completed_date");
    if (this.value === "Completed" && completed.value === "") {
        completed.value = today();
    }
});

// Due date cannot be before the created date
document.getElementById("created_date").addEventListener("change", function () {
    document.getElementById("due_date").min = this.value;
});

// Live character counter for the description
document.getElementById("description").addEventListener("input", function () {
    document.getElementById("desc-count").textContent = this.value.length;
});

// ---------------------------------------------------------------
// Create and edit
// ---------------------------------------------------------------

function openForm(titleText) {
    clearMessage();
    markInvalid(form, []);
    document.getElementById("form-title").textContent = titleText;
    openSheet(formCard);
}

document.getElementById("new-button").addEventListener("click", function () {
    form.reset();
    form.work_order_id.value = "";
    form.created_date.value = today();
    loadEquipmentDetails("");
    openForm("New work order");
});

async function editWorkOrder(id) {
    try {
        const wo = await apiRequest("GET", "/api/work_orders/" + id);
        form.reset();
        fillForm(form, wo);
        document.getElementById("desc-count").textContent = (wo.description || "").length;
        await loadEquipmentDetails(wo.equipment_id, wo.outage_id, wo.worker_id, wo.worker_name);
        openForm("Edit work order " + id);
    } catch (err) {
        showError(err);
    }
}

document.getElementById("cancel-button").addEventListener("click", function () {
    closeSheet(formCard);
});

// Check the form in the browser first, so the user gets quick feedback.
// The server checks everything again in validation.py.
function checkForm(data) {
    const errors = [];
    const badFields = [];

    if (!data.equipment_id) { errors.push("Choose a piece of equipment."); badFields.push("equipment_id"); }
    if (!data.title) { errors.push("Title is required."); badFields.push("title"); }
    if (!data.priority) { errors.push("Choose a priority."); badFields.push("priority"); }
    if (!data.created_date) { errors.push("Created date is required."); badFields.push("created_date"); }
    if (!data.due_date) { errors.push("Due date is required."); badFields.push("due_date"); }
    if (data.created_date && data.due_date && data.due_date < data.created_date) {
        errors.push("Due date cannot be before the created date."); badFields.push("due_date");
    }
    if (data.status === "Completed" && !data.completed_date) {
        errors.push("A completed work order needs a completed date."); badFields.push("completed_date");
    }
    return { errors, badFields };
}

form.addEventListener("submit", async function (event) {
    event.preventDefault();
    const data = formToObject(form);

    const check = checkForm(data);
    markInvalid(form, check.badFields);
    if (check.errors.length > 0) {
        showMessage("Please fix the following:", "error", check.errors);
        return;
    }

    const isNew = data.work_order_id === "";
    try {
        const result = isNew
            ? await apiRequest("POST", "/api/work_orders", data)
            : await apiRequest("PUT", "/api/work_orders/" + data.work_order_id, data);
        closeSheet(formCard);
        showMessage(result.message, "success");
        loadWorkOrders();
    } catch (err) {
        showError(err);
    }
});

// ---------------------------------------------------------------
// Delete (admin only)
// ---------------------------------------------------------------

async function deleteWorkOrder(id) {
    if (!confirm("Delete work order " + id + "? This cannot be undone.")) return;
    try {
        const result = await apiRequest("DELETE", "/api/work_orders/" + id);
        showMessage(result.message, "success");
        loadWorkOrders();
    } catch (err) {
        showError(err);
    }
}

setupPage();
