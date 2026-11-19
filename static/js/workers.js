// workers.js
// Workers page: list and search for everyone, create/edit/delete for admins.

const rowsBody = document.getElementById("rows");
const formCard = document.getElementById("form-card");
const form = document.getElementById("worker-form");
const EMAIL_PATTERN = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;

let emailTypedByUser = false;   // stop suggesting once the user types their own email

async function setupPage() {
    if (isAdmin()) document.getElementById("new-button").classList.remove("hidden");
    try {
        const stations = await apiRequest("GET", "/api/stations");
        fillSelect(document.getElementById("station_id"), stations, "station_id", s => s.name, "Choose a station...");
    } catch (err) {
        showError(err);
    }
    loadWorkers();
}

async function loadWorkers() {
    const keyword = document.getElementById("q").value.trim();
    let workers;
    try {
        workers = await apiRequest("GET", "/api/workers?q=" + encodeURIComponent(keyword));
    } catch (err) {
        showError(err);
        return;
    }

    if (workers.length === 0) {
        rowsBody.innerHTML = '<tr><td colspan="8" class="empty">No workers found.</td></tr>';
        return;
    }

    const todayDate = today();
    rowsBody.innerHTML = workers.map(w => {
        const expired = w.cert_expiry < todayDate;
        let buttons = "";
        if (isAdmin()) {
            buttons = '<button class="small secondary" onclick="editWorker(' + w.worker_id + ')">Edit</button> ' +
                      '<button class="small danger" onclick="deleteWorker(' + w.worker_id + ')">Delete</button>';
        }
        return "<tr>" +
            "<td>" + w.worker_id + "</td>" +
            "<td>" + escapeHtml(w.fname + " " + w.lname) + "</td>" +
            "<td>" + escapeHtml(w.trade) + "</td>" +
            "<td>" + escapeHtml(w.station_name) + "</td>" +
            "<td>" + escapeHtml(w.email) + "</td>" +
            '<td class="' + (expired ? "overdue" : "") + '">' + w.cert_expiry + (expired ? " (expired)" : "") + "</td>" +
            "<td>" + w.active_jobs + "</td>" +
            "<td>" + buttons + "</td>" +
            "</tr>";
    }).join("");
}

document.getElementById("search-form").addEventListener("submit", function (event) {
    event.preventDefault();
    loadWorkers();
});

// Auto-fill suggestion: build an email like "s.chen@nuclearops.ca" from the name
function suggestEmail() {
    if (emailTypedByUser) return;
    const first = form.fname.value.trim().toLowerCase();
    const last = form.lname.value.trim().toLowerCase().replace(/[^a-z]/g, "");
    if (first && last) form.email.value = first[0] + "." + last + "@nuclearops.ca";
}
form.fname.addEventListener("input", suggestEmail);
form.lname.addEventListener("input", suggestEmail);
form.email.addEventListener("input", () => { emailTypedByUser = true; });

// Check the email format as the user leaves the field
form.email.addEventListener("blur", function () {
    const ok = EMAIL_PATTERN.test(this.value.trim());
    this.classList.toggle("invalid", !ok);
    document.getElementById("email-hint").textContent = ok ? "Looks good." : "Please enter a valid email address.";
});

function openForm(titleText) {
    clearMessage();
    markInvalid(form, []);
    document.getElementById("form-title").textContent = titleText;
    openSheet(formCard);
}

document.getElementById("new-button").addEventListener("click", function () {
    form.reset();
    form.worker_id.value = "";
    emailTypedByUser = false;
    openForm("New worker");
});

async function editWorker(id) {
    try {
        const worker = await apiRequest("GET", "/api/workers/" + id);
        form.reset();
        fillForm(form, worker);
        emailTypedByUser = true;      // keep their existing email
        openForm("Edit worker " + id);
    } catch (err) {
        showError(err);
    }
}

document.getElementById("cancel-button").addEventListener("click", () => closeSheet(formCard));

form.addEventListener("submit", async function (event) {
    event.preventDefault();
    const data = formToObject(form);

    const errors = [];
    const badFields = [];
    for (const [field, label] of [["fname", "First name"], ["lname", "Last name"], ["trade", "Trade"],
                                  ["station_id", "Station"], ["cert_expiry", "Certification expiry"]]) {
        if (!data[field]) { errors.push(label + " is required."); badFields.push(field); }
    }
    if (!EMAIL_PATTERN.test(data.email)) {
        errors.push("Please enter a valid email address.");
        badFields.push("email");
    }
    markInvalid(form, badFields);
    if (errors.length > 0) {
        showMessage("Please fix the following:", "error", errors);
        return;
    }

    const isNew = data.worker_id === "";
    try {
        const result = isNew
            ? await apiRequest("POST", "/api/workers", data)
            : await apiRequest("PUT", "/api/workers/" + data.worker_id, data);
        closeSheet(formCard);
        showMessage(result.message, "success");
        loadWorkers();
    } catch (err) {
        showError(err);
    }
});

async function deleteWorker(id) {
    if (!confirm("Delete worker " + id + "? Their work orders will become unassigned.")) return;
    try {
        const result = await apiRequest("DELETE", "/api/workers/" + id);
        showMessage(result.message, "success");
        loadWorkers();
    } catch (err) {
        showError(err);
    }
}

setupPage();
