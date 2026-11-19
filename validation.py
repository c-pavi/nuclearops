# validation.py
# Checks user input before it is saved to the database.
# Each function returns a list of error messages. An empty list means the input is valid.

import re
from datetime import date
import db

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PRIORITIES = ["Low", "Medium", "High", "Critical"]
WO_STATUSES = ["Open", "In Progress", "Completed", "Cancelled"]


# ---------- small helpers ----------

def to_int(value):
    """Turn a value into an int, or return None if it is empty or not a number."""
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(value)
    except (ValueError, TypeError):
        return None


def to_date(value):
    """Turn a 'YYYY-MM-DD' string into a date, or return None if it is not a valid date."""
    try:
        return date.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None


def check_required(data, field, label, max_length, errors):
    """Check that a text field is filled in and not too long."""
    value = str(data.get(field) or "").strip()
    if value == "":
        errors.append(label + " is required.")
    elif len(value) > max_length:
        errors.append(label + " must be " + str(max_length) + " characters or less.")


def exists(table, id_column, value):
    """Return True if a row with this id exists. table and id_column come from our code only."""
    row = db.query("SELECT 1 FROM " + table + " WHERE " + id_column + " = %s", (value,), one=True)
    return row is not None


# ---------- work orders ----------

def validate_work_order(data):
    errors = []

    equipment_id = to_int(data.get("equipment_id"))
    if equipment_id is None:
        errors.append("Equipment is required.")
    elif not exists("EQUIPMENT", "Equipment_id", equipment_id):
        errors.append("The selected equipment does not exist.")

    # Outage and worker are optional, but must exist if given
    if data.get("outage_id") not in (None, ""):
        outage_id = to_int(data.get("outage_id"))
        if outage_id is None or not exists("OUTAGE", "Outage_id", outage_id):
            errors.append("The selected outage does not exist.")
    if data.get("worker_id") not in (None, ""):
        worker_id = to_int(data.get("worker_id"))
        if worker_id is None or not exists("WORKER", "Worker_id", worker_id):
            errors.append("The selected worker does not exist.")

    check_required(data, "title", "Title", 100, errors)
    if len(str(data.get("description") or "")) > 255:
        errors.append("Description must be 255 characters or less.")

    if data.get("priority") not in PRIORITIES:
        errors.append("Priority must be one of: " + ", ".join(PRIORITIES) + ".")
    if data.get("status") not in WO_STATUSES:
        errors.append("Status must be one of: " + ", ".join(WO_STATUSES) + ".")

    created = to_date(data.get("created_date"))
    due = to_date(data.get("due_date"))
    if created is None:
        errors.append("Created date must be a valid date (YYYY-MM-DD).")
    if due is None:
        errors.append("Due date must be a valid date (YYYY-MM-DD).")
    if created and due and due < created:
        errors.append("Due date cannot be before the created date.")

    completed_raw = data.get("completed_date")
    if completed_raw not in (None, ""):
        completed = to_date(completed_raw)
        if completed is None:
            errors.append("Completed date must be a valid date (YYYY-MM-DD).")
        elif created and completed < created:
            errors.append("Completed date cannot be before the created date.")
    elif data.get("status") == "Completed":
        errors.append("A completed work order needs a completed date.")

    return errors


# ---------- workers ----------

def validate_worker(data, worker_id=None):
    errors = []

    station_id = to_int(data.get("station_id"))
    if station_id is None or not exists("STATION", "Station_id", station_id):
        errors.append("Please choose a valid station.")

    check_required(data, "fname", "First name", 20, errors)
    check_required(data, "lname", "Last name", 20, errors)
    check_required(data, "trade", "Trade", 20, errors)

    email = str(data.get("email") or "").strip()
    if not EMAIL_PATTERN.match(email):
        errors.append("Please enter a valid email address (for example name@nuclearops.ca).")
    elif len(email) > 50:
        errors.append("Email must be 50 characters or less.")
    else:
        # Email must be unique (another worker cannot already use it)
        other = db.query("SELECT Worker_id FROM WORKER WHERE Email = %s", (email,), one=True)
        if other and other["worker_id"] != worker_id:
            errors.append("Another worker already uses this email.")

    if to_date(data.get("cert_expiry")) is None:
        errors.append("Certification expiry must be a valid date (YYYY-MM-DD).")

    return errors


# ---------- equipment ----------

def validate_equipment(data, equipment_id=None):
    errors = []

    system_id = to_int(data.get("system_id"))
    if system_id is None or not exists("PLANT_SYSTEM", "System_id", system_id):
        errors.append("Please choose a valid plant system.")

    check_required(data, "tag_number", "Tag number", 20, errors)
    check_required(data, "name", "Name", 50, errors)
    check_required(data, "equipment_type", "Equipment type", 20, errors)
    if len(str(data.get("manufacturer") or "")) > 50:
        errors.append("Manufacturer must be 50 characters or less.")

    tag = str(data.get("tag_number") or "").strip()
    if tag:
        other = db.query("SELECT Equipment_id FROM EQUIPMENT WHERE Tag_number = %s", (tag,), one=True)
        if other and other["equipment_id"] != equipment_id:
            errors.append("Another piece of equipment already uses this tag number.")

    if to_date(data.get("install_date")) is None:
        errors.append("Install date must be a valid date (YYYY-MM-DD).")

    interval = to_int(data.get("inspection_interval_days"))
    if interval is None or interval <= 0:
        errors.append("Inspection interval must be a whole number greater than 0.")

    return errors
