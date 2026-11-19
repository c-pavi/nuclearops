// common.js
// Small helper functions used by every page.

// Send a request to our REST API and return the JSON response.
// If the server sends back an error, this throws it so the page can show it.
async function apiRequest(method, url, body) {
    const options = { method: method, headers: {} };
    if (body !== undefined) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(body);
    }

    let response;
    try {
        response = await fetch(url, options);
    } catch (networkError) {
        throw { error: "Could not reach the server. Is the app still running?" };
    }

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw data.error ? data : { error: "Request failed (status " + response.status + ")." };
    }
    return data;
}

// ---------------------------------------------------------------
// Springs
// A tiny spring animator described the way Apple does it: a damping ratio
// (1 = no bounce, below 1 = some overshoot) and a response in seconds.
// Springs start from the current value and keep the current velocity,
// so a moving element can be grabbed or redirected at any moment.
// ---------------------------------------------------------------
const REDUCED_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)");

function createSpring(initial, onUpdate) {
    const spring = { value: initial, velocity: 0, target: initial, frame: null, done: null };

    function step(dt) {
        const k = Math.pow(2 * Math.PI / spring.response, 2);       // stiffness (mass = 1)
        const c = 4 * Math.PI * spring.damping / spring.response;   // damping
        const force = -k * (spring.value - spring.target) - c * spring.velocity;
        spring.velocity += force * dt;
        spring.value += spring.velocity * dt;
    }

    spring.to = function (target, options) {
        options = options || {};
        spring.target = target;
        spring.damping = options.damping !== undefined ? options.damping : 1;
        spring.response = options.response || 0.35;
        if (options.velocity !== undefined) spring.velocity = options.velocity;
        spring.done = options.done || null;
        cancelAnimationFrame(spring.frame);

        if (REDUCED_MOTION.matches) {
            spring.value = target;
            spring.velocity = 0;
            onUpdate(target);
            if (spring.done) spring.done();
            return;
        }

        let last = performance.now();
        const tick = function (now) {
            let dt = Math.min((now - last) / 1000, 0.064);
            last = now;
            while (dt > 0) { const h = Math.min(dt, 1 / 240); step(h); dt -= h; }
            const settled = Math.abs(spring.velocity) < 2 && Math.abs(spring.value - spring.target) < 0.5;
            if (settled) {
                spring.value = spring.target;
                spring.velocity = 0;
                onUpdate(spring.value);
                if (spring.done) spring.done();
                return;
            }
            onUpdate(spring.value);
            spring.frame = requestAnimationFrame(tick);
        };
        spring.frame = requestAnimationFrame(tick);
    };

    spring.set = function (value) {
        cancelAnimationFrame(spring.frame);
        spring.value = value;
        spring.velocity = 0;
        onUpdate(value);
    };

    spring.stop = function () { cancelAnimationFrame(spring.frame); };
    return spring;
}

// Where a flick will come to rest (Apple's scroll-deceleration projection)
function projectMomentum(velocity, decelerationRate) {
    decelerationRate = decelerationRate || 0.998;
    return (velocity / 1000) * decelerationRate / (1 - decelerationRate);
}

// Resistance past a boundary: the further you pull, the less it follows
function rubberband(overshoot, dimension) {
    const constant = 0.55;
    return (overshoot * dimension * constant) / (dimension + constant * Math.abs(overshoot));
}

// ---------------------------------------------------------------
// Sheets: create/edit forms slide up from the bottom and can be
// dragged down (or flicked) to dismiss.
// ---------------------------------------------------------------
let scrim = null;
let openSheetCard = null;

function getScrim() {
    if (!scrim) {
        scrim = document.createElement("div");
        scrim.className = "scrim";
        scrim.addEventListener("click", () => openSheetCard && closeSheet(openSheetCard));
        document.body.appendChild(scrim);
    }
    return scrim;
}

function setupSheet(card) {
    if (card.sheetSpring) return;
    card.classList.add("sheet");
    card.setAttribute("role", "dialog");
    card.setAttribute("aria-modal", "true");

    const grabber = document.createElement("div");
    grabber.className = "sheet-grabber";
    grabber.setAttribute("aria-hidden", "true");
    card.prepend(grabber);

    const closedOffset = () => card.offsetHeight + 40;

    card.sheetSpring = createSpring(0, function (y) {
        card.style.transform = "translate(-50%, " + y + "px)";
        const progress = Math.max(0, Math.min(1, 1 - y / closedOffset()));
        getScrim().style.opacity = progress;
    });

    // Drag to dismiss: the sheet follows the pointer 1:1 from where it was grabbed
    let drag = null;
    const startDrag = function (event) {
        if (event.button !== 0) return;
        drag = { startY: event.clientY, startValue: card.sheetSpring.value, history: [] };
        card.sheetSpring.stop();
        event.currentTarget.setPointerCapture(event.pointerId);
    };
    const moveDrag = function (event) {
        if (!drag) return;
        let y = drag.startValue + (event.clientY - drag.startY);
        if (y < 0) y = rubberband(y, card.offsetHeight);   // soft edge when pulled up
        card.sheetSpring.set(y);
        drag.history.push({ y: event.clientY, t: event.timeStamp });
        if (drag.history.length > 6) drag.history.shift();
    };
    const endDrag = function () {
        if (!drag) return;
        const h = drag.history;
        let velocity = 0;
        if (h.length >= 2) {
            const a = h[0], b = h[h.length - 1];
            if (b.t - a.t > 0) velocity = (b.y - a.y) / (b.t - a.t) * 1000;   // px/s
        }
        drag = null;
        const y = card.sheetSpring.value;
        const projected = y + projectMomentum(velocity, 0.99);
        if (projected > closedOffset() * 0.4) {
            closeSheet(card, velocity);
        } else {
            card.sheetSpring.to(0, { damping: 0.8, response: 0.3, velocity: velocity });
        }
    };
    for (const handle of [grabber, card.querySelector("h2")]) {
        if (!handle) continue;
        handle.style.touchAction = "none";
        handle.addEventListener("pointerdown", startDrag);
        handle.addEventListener("pointermove", moveDrag);
        handle.addEventListener("pointerup", endDrag);
        handle.addEventListener("pointercancel", endDrag);
    }
}

function openSheet(card) {
    setupSheet(card);
    const wasHidden = card.classList.contains("hidden");
    card.classList.remove("hidden");
    openSheetCard = card;
    document.body.classList.add("sheet-open");
    getScrim().classList.add("visible");
    if (wasHidden) {
        card.scrollTop = 0;
        card.sheetSpring.set(card.offsetHeight + 40);
    }
    // No bounce: nothing was thrown, so the sheet simply arrives
    card.sheetSpring.to(0, { damping: 1, response: 0.38 });
    const first = card.querySelector("input:not([type=hidden]), select, textarea");
    if (first) first.focus({ preventScroll: true });
}

function closeSheet(card, velocity) {
    if (!card.sheetSpring) { card.classList.add("hidden"); return; }
    openSheetCard = null;
    document.body.classList.remove("sheet-open");
    getScrim().classList.remove("visible");
    // Leaves the way it came: back down. A flick keeps its speed.
    card.sheetSpring.to(card.offsetHeight + 40, {
        damping: 1,
        response: 0.32,
        velocity: velocity,
        done: () => { if (openSheetCard !== card) card.classList.add("hidden"); },
    });
}

document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && openSheetCard) closeSheet(openSheetCard);
});

// ---------------------------------------------------------------
// Messages: floating toasts at the top of the page.
// Success and info fade away on their own; errors stay until closed.
// ---------------------------------------------------------------
function presentToast(toast, type) {
    if (!toast.querySelector(".close")) {
        const close = document.createElement("button");
        close.type = "button";
        close.className = "close";
        close.setAttribute("aria-label", "Dismiss");
        close.textContent = "\u2715";
        close.addEventListener("click", () => dismissToast(toast));
        toast.appendChild(close);
    }
    const spring = createSpring(-24, function (y) {
        toast.style.transform = "translateY(" + y + "px)";
        toast.style.opacity = Math.max(0, Math.min(1, 1 + y / 24));
    });
    toast.toastSpring = spring;
    spring.set(-24);
    spring.to(0, { damping: 1, response: 0.35 });
    if (type !== "error") toast.toastTimer = setTimeout(() => dismissToast(toast), 4500);
}

function dismissToast(toast) {
    clearTimeout(toast.toastTimer);
    if (!toast.toastSpring) { toast.remove(); return; }
    toast.toastSpring.to(-24, { damping: 1, response: 0.28, done: () => toast.remove() });
}

function showMessage(text, type, details) {
    const area = document.getElementById("message-area");
    let html = escapeHtml(text);
    if (details && details.length > 0) {
        html += "<ul>" + details.map(d => "<li>" + escapeHtml(d) + "</li>").join("") + "</ul>";
    }
    area.querySelectorAll(".message").forEach(dismissToast);
    const toast = document.createElement("div");
    toast.className = "message " + (type || "info");
    toast.innerHTML = html;
    area.appendChild(toast);
    presentToast(toast, type);
}

function showError(err) {
    showMessage(err.error || "Something went wrong.", "error", err.details);
}

function clearMessage() {
    document.getElementById("message-area").querySelectorAll(".message").forEach(dismissToast);
}

// Flashed messages from the server get the same toast behaviour
document.querySelectorAll("#message-area .message").forEach(t => presentToast(t, "info"));

// ---------------------------------------------------------------
// Chart.js styling to match the system look (light and dark)
// ---------------------------------------------------------------
function cssColor(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function applyChartTheme() {
    if (!window.Chart) return;
    Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif';
    Chart.defaults.font.size = 12;
    Chart.defaults.color = cssColor("--muted");
    Chart.defaults.borderColor = cssColor("--separator");
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.pointStyle = "circle";
    Chart.defaults.plugins.legend.labels.boxWidth = 8;
    Chart.defaults.plugins.legend.labels.boxHeight = 8;
    Chart.defaults.plugins.tooltip.cornerRadius = 10;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.elements.bar.borderRadius = 6;
    Chart.defaults.elements.bar.borderSkipped = false;
    Chart.defaults.elements.line.tension = 0.35;
    Chart.defaults.elements.line.borderWidth = 2.5;
    Chart.defaults.elements.point.radius = 0;
    Chart.defaults.elements.point.hoverRadius = 5;
    Chart.defaults.scale.grid.drawTicks = false;
    Chart.defaults.scale.border.display = false;
    Chart.defaults.animation.duration = REDUCED_MOTION.matches ? 0 : 600;
}

// Stop text from the database being treated as HTML (prevents XSS).
function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

// Show "-" for empty values in tables.
function show(value) {
    return (value === null || value === undefined || value === "") ? "-" : escapeHtml(value);
}

// Coloured label for a priority or status, e.g. <span class="tag High">High</span>
function tag(value) {
    return '<span class="tag ' + escapeHtml(String(value).replace(" ", "-")) + '">' + escapeHtml(value) + "</span>";
}

// Today's date as "YYYY-MM-DD" (the format used by <input type="date">).
function today() {
    const d = new Date();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return d.getFullYear() + "-" + month + "-" + day;
}

// Fill a <select> with options from a list of objects.
function fillSelect(select, items, valueKey, labelFunction, firstOption) {
    let html = firstOption !== undefined ? '<option value="">' + escapeHtml(firstOption) + "</option>" : "";
    for (const item of items) {
        html += '<option value="' + escapeHtml(item[valueKey]) + '">' + escapeHtml(labelFunction(item)) + "</option>";
    }
    select.innerHTML = html;
}

// Read every input in a form into an object: { field_name: value }
function formToObject(form) {
    const data = {};
    for (const element of form.elements) {
        if (element.name) data[element.name] = element.value.trim();
    }
    return data;
}

// Put an object's values back into a form's inputs (used when editing).
function fillForm(form, data) {
    for (const element of form.elements) {
        if (element.name && data[element.name] !== undefined) {
            element.value = data[element.name] === null ? "" : data[element.name];
        }
    }
}

// Mark which inputs have problems (red border).
function markInvalid(form, fieldNames) {
    for (const element of form.elements) {
        element.classList.toggle("invalid", fieldNames.includes(element.name));
    }
}

// Remove the red border from a field as soon as the user changes it
document.addEventListener("input", event => event.target.classList.remove("invalid"));
document.addEventListener("change", event => event.target.classList.remove("invalid"));

function canEdit() { return CURRENT_ROLE === "admin" || CURRENT_ROLE === "user"; }
function isAdmin() { return CURRENT_ROLE === "admin"; }
