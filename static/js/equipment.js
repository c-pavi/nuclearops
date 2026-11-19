// equipment.js
// Equipment page: list and search for everyone, create/edit/delete for admins.

const rowsBody = document.getElementById("rows");
const formCard = document.getElementById("form-card");
const form = document.getElementById("equipment-form");

async function setupPage() {
    if (isAdmin()) document.getElementById("new-button").classList.remove("hidden");
    try {
        const systems = await apiRequest("GET", "/api/systems");
        fillSelect(document.getElementById("system_id"), systems, "system_id",
                   s => s.station_name + " Unit " + s.unit_number + " - " + s.name, "Choose a system...");
    } catch (err) {
        showError(err);
    }
    loadEquipment();
}

async function loadEquipment() {
    const keyword = document.getElementById("q").value.trim();
    let items;
    try {
        items = await apiRequest("GET", "/api/equipment?q=" + encodeURIComponent(keyword));
    } catch (err) {
        showError(err);
        return;
    }

    if (items.length === 0) {
        rowsBody.innerHTML = '<tr><td colspan="9" class="empty">No equipment found.</td></tr>';
        return;
    }

    rowsBody.innerHTML = items.map(e => {
        let buttons = "";
        if (isAdmin()) {
            buttons = '<button class="small secondary" onclick="editEquipment(' + e.equipment_id + ')">Edit</button> ' +
                      '<button class="small danger" onclick="deleteEquipment(' + e.equipment_id + ')">Delete</button>';
        }
        return "<tr>" +
            "<td>" + e.equipment_id + "</td>" +
            "<td>" + escapeHtml(e.tag_number) + "</td>" +
            "<td>" + escapeHtml(e.name) + "</td>" +
            "<td>" + escapeHtml(e.equipment_type) + "</td>" +
            "<td>" + escapeHtml(e.station_name) + " U" + e.unit_number + ", " + escapeHtml(e.system_name) + "</td>" +
            "<td>" + show(e.manufacturer) + "</td>" +
            "<td>" + e.install_date + "</td>" +
            "<td>" + e.inspection_interval_days + " days</td>" +
            "<td>" + buttons + "</td>" +
            "</tr>";
    }).join("");
}

document.getElementById("search-form").addEventListener("submit", function (event) {
    event.preventDefault();
    loadEquipment();
});

function openForm(titleText) {
    clearMessage();
    markInvalid(form, []);
    document.getElementById("form-title").textContent = titleText;
    openSheet(formCard);
}

document.getElementById("new-button").addEventListener("click", function () {
    form.reset();
    form.equipment_id.value = "";
    openForm("New equipment");
});

async function editEquipment(id) {
    try {
        const item = await apiRequest("GET", "/api/equipment/" + id);
        form.reset();
        fillForm(form, item);
        openForm("Edit equipment " + id);
    } catch (err) {
        showError(err);
    }
}

document.getElementById("cancel-button").addEventListener("click", () => closeSheet(formCard));

form.addEventListener("submit", async function (event) {
    event.preventDefault();
    const data = formToObject(form);

    // Quick checks in the browser (the server checks again)
    const errors = [];
    const badFields = [];
    for (const [field, label] of [["tag_number", "Tag number"], ["name", "Name"], ["equipment_type", "Type"],
                                  ["system_id", "Plant system"], ["install_date", "Install date"]]) {
        if (!data[field]) { errors.push(label + " is required."); badFields.push(field); }
    }
    if (!(parseInt(data.inspection_interval_days) > 0)) {
        errors.push("Inspection interval must be a whole number greater than 0.");
        badFields.push("inspection_interval_days");
    }
    markInvalid(form, badFields);
    if (errors.length > 0) {
        showMessage("Please fix the following:", "error", errors);
        return;
    }

    const isNew = data.equipment_id === "";
    try {
        const result = isNew
            ? await apiRequest("POST", "/api/equipment", data)
            : await apiRequest("PUT", "/api/equipment/" + data.equipment_id, data);
        closeSheet(formCard);
        showMessage(result.message, "success");
        loadEquipment();
    } catch (err) {
        showError(err);
    }
});

async function deleteEquipment(id) {
    if (!confirm("Delete equipment " + id + "? Its work orders and inspections will also be deleted.")) return;
    try {
        const result = await apiRequest("DELETE", "/api/equipment/" + id);
        showMessage(result.message, "success");
        loadEquipment();
    } catch (err) {
        showError(err);
    }
}

setupPage();
