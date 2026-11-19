# api.py
# REST/JSON web service for NuclearOps.
# The web pages use these endpoints with JavaScript fetch() so they can
# load and save data without reloading the page.
#
#   GET     /api/work_orders            list (with search and filters)
#   GET     /api/work_orders/<id>       one work order
#   POST    /api/work_orders            create
#   PUT     /api/work_orders/<id>       update
#   DELETE  /api/work_orders/<id>       delete
#   (the same pattern is used for /api/equipment and /api/workers)
#
#   GET     /api/outages/<id>/weather   saved weather for an outage
#   POST    /api/outages/<id>/weather   get weather from Open-Meteo and save it

from flask import Blueprint, request, jsonify, session
import db
import validation
import weather
from auth import login_required, role_required
from validation import to_int

api = Blueprint("api", __name__, url_prefix="/api")


def blank_to_none(value):
    """Empty form fields should be saved as NULL, not as empty text."""
    if value is None or str(value).strip() == "":
        return None
    return value


def bad_request(errors):
    return jsonify({"error": "Please fix the following:", "details": errors}), 400


def not_found(what):
    return jsonify({"error": what + " not found."}), 404


# =====================================================================
# Lookup lists (used to fill dropdown menus)
# =====================================================================

@api.route("/stations", methods=["GET"])
@login_required
def list_stations():
    return jsonify(db.query("SELECT Station_id, Name FROM STATION ORDER BY Name"))


@api.route("/systems", methods=["GET"])
@login_required
def list_systems():
    rows = db.query("""
        SELECT  PS.System_id, PS.Name, S.Name AS Station_name, R.Unit_number
        FROM    PLANT_SYSTEM AS PS
            JOIN REACTOR_UNIT AS R  ON PS.Unit_id = R.Unit_id
            JOIN STATION AS S       ON R.Station_id = S.Station_id
        ORDER BY S.Name, R.Unit_number, PS.Name
    """)
    return jsonify(rows)


@api.route("/outages", methods=["GET"])
@login_required
def list_outages():
    rows = db.query("""
        SELECT  O.Outage_id, O.Outage_type, O.Status, O.Start_date, O.Planned_end_date,
                S.Name AS Station_name, R.Unit_number
        FROM    OUTAGE AS O
            JOIN REACTOR_UNIT AS R  ON O.Unit_id = R.Unit_id
            JOIN STATION AS S       ON R.Station_id = S.Station_id
        ORDER BY CASE O.Status WHEN 'In Progress' THEN 1 WHEN 'Scheduled' THEN 2 ELSE 3 END,
                 O.Start_date DESC
    """)
    return jsonify(rows)


# =====================================================================
# Work orders
# =====================================================================

WORK_ORDER_SELECT = """
    SELECT  WO.Work_order_id, WO.Equipment_id, WO.Outage_id, WO.Worker_id,
            WO.Title, WO.Description, WO.Priority, WO.Status,
            WO.Created_date, WO.Due_date, WO.Completed_date,
            E.Tag_number, E.Name AS Equipment_name,
            S.Station_id, S.Name AS Station_name, R.Unit_number,
            W.Fname || ' ' || W.Lname AS Worker_name
    FROM    WORK_ORDER AS WO
        JOIN EQUIPMENT AS E         ON WO.Equipment_id = E.Equipment_id
        JOIN PLANT_SYSTEM AS PS     ON E.System_id = PS.System_id
        JOIN REACTOR_UNIT AS R      ON PS.Unit_id = R.Unit_id
        JOIN STATION AS S           ON R.Station_id = S.Station_id
        LEFT JOIN WORKER AS W       ON WO.Worker_id = W.Worker_id
"""


@api.route("/work_orders", methods=["GET"])
@login_required
def list_work_orders():
    # Build the WHERE clause from whichever filters were sent.
    # Values always go in params (never pasted into the SQL) to prevent SQL injection.
    conditions = []
    params = []

    keyword = request.args.get("q", "").strip()
    if keyword:
        conditions.append("(WO.Title ILIKE %s OR E.Name ILIKE %s OR E.Tag_number ILIKE %s)")
        params += ["%" + keyword + "%"] * 3

    if request.args.get("status"):
        conditions.append("WO.Status = %s")
        params.append(request.args["status"])
    if request.args.get("priority"):
        conditions.append("WO.Priority = %s")
        params.append(request.args["priority"])
    if to_int(request.args.get("station_id")) is not None:
        conditions.append("S.Station_id = %s")
        params.append(to_int(request.args["station_id"]))
    if validation.to_date(request.args.get("due_from")):
        conditions.append("WO.Due_date >= %s")
        params.append(request.args["due_from"])
    if validation.to_date(request.args.get("due_to")):
        conditions.append("WO.Due_date <= %s")
        params.append(request.args["due_to"])

    sql = WORK_ORDER_SELECT
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY WO.Due_date"

    return jsonify(db.query(sql, params))


@api.route("/work_orders/<int:work_order_id>", methods=["GET"])
@login_required
def get_work_order(work_order_id):
    row = db.query(WORK_ORDER_SELECT + " WHERE WO.Work_order_id = %s", (work_order_id,), one=True)
    if row is None:
        return not_found("Work order")
    return jsonify(row)


def work_order_values(data):
    return (
        to_int(data["equipment_id"]),
        to_int(blank_to_none(data.get("outage_id"))),
        to_int(blank_to_none(data.get("worker_id"))),
        data["title"].strip(),
        blank_to_none(data.get("description")),
        data["priority"],
        data["status"],
        data["created_date"],
        data["due_date"],
        blank_to_none(data.get("completed_date")),
    )


@api.route("/work_orders", methods=["POST"])
@role_required("admin", "user")
def create_work_order():
    data = request.get_json(silent=True)
    if data is None:
        return bad_request(["Request body must be JSON."])
    errors = validation.validate_work_order(data)
    if errors:
        return bad_request(errors)

    new_id = db.next_id("WORK_ORDER", "Work_order_id")
    db.execute("""
        INSERT INTO WORK_ORDER (Work_order_id, Equipment_id, Outage_id, Worker_id, Title, Description,
                                Priority, Status, Created_date, Due_date, Completed_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (new_id,) + work_order_values(data))
    return jsonify({"message": "Work order " + str(new_id) + " created.", "work_order_id": new_id}), 201


@api.route("/work_orders/<int:work_order_id>", methods=["PUT"])
@role_required("admin", "user")
def update_work_order(work_order_id):
    data = request.get_json(silent=True)
    if data is None:
        return bad_request(["Request body must be JSON."])
    errors = validation.validate_work_order(data)
    if errors:
        return bad_request(errors)

    count = db.execute("""
        UPDATE  WORK_ORDER
        SET     Equipment_id = %s, Outage_id = %s, Worker_id = %s, Title = %s, Description = %s,
                Priority = %s, Status = %s, Created_date = %s, Due_date = %s, Completed_date = %s
        WHERE   Work_order_id = %s
    """, work_order_values(data) + (work_order_id,))
    if count == 0:
        return not_found("Work order")
    return jsonify({"message": "Work order " + str(work_order_id) + " updated."})


@api.route("/work_orders/<int:work_order_id>", methods=["DELETE"])
@role_required("admin")
def delete_work_order(work_order_id):
    count = db.execute("DELETE FROM WORK_ORDER WHERE Work_order_id = %s", (work_order_id,))
    if count == 0:
        return not_found("Work order")
    return jsonify({"message": "Work order " + str(work_order_id) + " deleted."})


# =====================================================================
# Equipment
# =====================================================================

@api.route("/equipment", methods=["GET"])
@login_required
def list_equipment():
    keyword = request.args.get("q", "").strip()
    sql = """
        SELECT  E.Equipment_id, E.System_id, E.Tag_number, E.Name, E.Equipment_type,
                E.Manufacturer, E.Install_date, E.Inspection_interval_days,
                PS.Name AS System_name, S.Name AS Station_name, R.Unit_number
        FROM    EQUIPMENT AS E
            JOIN PLANT_SYSTEM AS PS  ON E.System_id = PS.System_id
            JOIN REACTOR_UNIT AS R   ON PS.Unit_id = R.Unit_id
            JOIN STATION AS S        ON R.Station_id = S.Station_id
    """
    params = []
    if keyword:
        sql += " WHERE E.Name ILIKE %s OR E.Tag_number ILIKE %s OR E.Equipment_type ILIKE %s"
        params = ["%" + keyword + "%"] * 3
    sql += " ORDER BY E.Equipment_id"
    return jsonify(db.query(sql, params))


@api.route("/equipment/<int:equipment_id>", methods=["GET"])
@login_required
def get_equipment(equipment_id):
    """Returns one piece of equipment plus the outages for its reactor unit and the
    workers at its station. The work order form uses this to auto-fill its dropdowns."""
    item = db.query("""
        SELECT  E.*, PS.Name AS System_name, R.Unit_id, R.Unit_number,
                S.Station_id, S.Name AS Station_name
        FROM    EQUIPMENT AS E
            JOIN PLANT_SYSTEM AS PS  ON E.System_id = PS.System_id
            JOIN REACTOR_UNIT AS R   ON PS.Unit_id = R.Unit_id
            JOIN STATION AS S        ON R.Station_id = S.Station_id
        WHERE   E.Equipment_id = %s
    """, (equipment_id,), one=True)
    if item is None:
        return not_found("Equipment")

    item["outages"] = db.query("""
        SELECT Outage_id, Outage_type, Status, Start_date
        FROM   OUTAGE
        WHERE  Unit_id = %s AND Status <> 'Completed'
        ORDER BY Start_date
    """, (item["unit_id"],))

    item["workers"] = db.query("""
        SELECT Worker_id, Fname, Lname, Trade, Cert_expiry
        FROM   WORKER
        WHERE  Station_id = %s AND Cert_expiry >= CURRENT_DATE
        ORDER BY Lname
    """, (item["station_id"],))
    return jsonify(item)


def equipment_values(data):
    return (
        to_int(data["system_id"]),
        data["tag_number"].strip(),
        data["name"].strip(),
        data["equipment_type"].strip(),
        blank_to_none(data.get("manufacturer")),
        data["install_date"],
        to_int(data["inspection_interval_days"]),
    )


@api.route("/equipment", methods=["POST"])
@role_required("admin")
def create_equipment():
    data = request.get_json(silent=True)
    if data is None:
        return bad_request(["Request body must be JSON."])
    errors = validation.validate_equipment(data)
    if errors:
        return bad_request(errors)

    new_id = db.next_id("EQUIPMENT", "Equipment_id")
    db.execute("""
        INSERT INTO EQUIPMENT (Equipment_id, System_id, Tag_number, Name, Equipment_type,
                               Manufacturer, Install_date, Inspection_interval_days)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (new_id,) + equipment_values(data))
    return jsonify({"message": "Equipment " + str(new_id) + " created.", "equipment_id": new_id}), 201


@api.route("/equipment/<int:equipment_id>", methods=["PUT"])
@role_required("admin")
def update_equipment(equipment_id):
    data = request.get_json(silent=True)
    if data is None:
        return bad_request(["Request body must be JSON."])
    errors = validation.validate_equipment(data, equipment_id)
    if errors:
        return bad_request(errors)

    count = db.execute("""
        UPDATE  EQUIPMENT
        SET     System_id = %s, Tag_number = %s, Name = %s, Equipment_type = %s,
                Manufacturer = %s, Install_date = %s, Inspection_interval_days = %s
        WHERE   Equipment_id = %s
    """, equipment_values(data) + (equipment_id,))
    if count == 0:
        return not_found("Equipment")
    return jsonify({"message": "Equipment " + str(equipment_id) + " updated."})


@api.route("/equipment/<int:equipment_id>", methods=["DELETE"])
@role_required("admin")
def delete_equipment(equipment_id):
    # ON DELETE CASCADE also removes this equipment's work orders and inspections
    count = db.execute("DELETE FROM EQUIPMENT WHERE Equipment_id = %s", (equipment_id,))
    if count == 0:
        return not_found("Equipment")
    return jsonify({"message": "Equipment " + str(equipment_id) + " deleted."})


# =====================================================================
# Workers
# =====================================================================

@api.route("/workers", methods=["GET"])
@login_required
def list_workers():
    keyword = request.args.get("q", "").strip()
    sql = """
        SELECT  W.Worker_id, W.Station_id, W.Fname, W.Lname, W.Email, W.Trade, W.Cert_expiry,
                S.Name AS Station_name,
                (SELECT COUNT(*) FROM WORK_ORDER AS WO
                 WHERE WO.Worker_id = W.Worker_id AND WO.Status IN ('Open', 'In Progress')) AS Active_jobs
        FROM    WORKER AS W
            JOIN STATION AS S  ON W.Station_id = S.Station_id
    """
    params = []
    if keyword:
        sql += " WHERE W.Fname ILIKE %s OR W.Lname ILIKE %s OR W.Trade ILIKE %s"
        params = ["%" + keyword + "%"] * 3
    sql += " ORDER BY W.Worker_id"
    return jsonify(db.query(sql, params))


@api.route("/workers/<int:worker_id>", methods=["GET"])
@login_required
def get_worker(worker_id):
    row = db.query("SELECT * FROM WORKER WHERE Worker_id = %s", (worker_id,), one=True)
    if row is None:
        return not_found("Worker")
    return jsonify(row)


def worker_values(data):
    return (
        to_int(data["station_id"]),
        data["fname"].strip(),
        data["lname"].strip(),
        data["email"].strip(),
        data["trade"].strip(),
        data["cert_expiry"],
    )


@api.route("/workers", methods=["POST"])
@role_required("admin")
def create_worker():
    data = request.get_json(silent=True)
    if data is None:
        return bad_request(["Request body must be JSON."])
    errors = validation.validate_worker(data)
    if errors:
        return bad_request(errors)

    new_id = db.next_id("WORKER", "Worker_id")
    db.execute("""
        INSERT INTO WORKER (Worker_id, Station_id, Fname, Lname, Email, Trade, Cert_expiry)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (new_id,) + worker_values(data))
    return jsonify({"message": "Worker " + str(new_id) + " created.", "worker_id": new_id}), 201


@api.route("/workers/<int:worker_id>", methods=["PUT"])
@role_required("admin")
def update_worker(worker_id):
    data = request.get_json(silent=True)
    if data is None:
        return bad_request(["Request body must be JSON."])
    errors = validation.validate_worker(data, worker_id)
    if errors:
        return bad_request(errors)

    count = db.execute("""
        UPDATE  WORKER
        SET     Station_id = %s, Fname = %s, Lname = %s, Email = %s, Trade = %s, Cert_expiry = %s
        WHERE   Worker_id = %s
    """, worker_values(data) + (worker_id,))
    if count == 0:
        return not_found("Worker")
    return jsonify({"message": "Worker " + str(worker_id) + " updated."})


@api.route("/workers/<int:worker_id>", methods=["DELETE"])
@role_required("admin")
def delete_worker(worker_id):
    # Their work orders become unassigned (ON DELETE SET NULL)
    count = db.execute("DELETE FROM WORKER WHERE Worker_id = %s", (worker_id,))
    if count == 0:
        return not_found("Worker")
    return jsonify({"message": "Worker " + str(worker_id) + " deleted."})


# =====================================================================
# Weather (external API)
# =====================================================================

@api.route("/outages/<int:outage_id>/weather", methods=["GET"])
@login_required
def get_outage_weather(outage_id):
    """Returns the weather saved for one outage, plus a summary."""
    readings = db.query("""
        SELECT  Weather_id, Recorded_at, Temperature_c, Wind_speed_kmh, Precip_mm, Conditions
        FROM    WEATHER_LOG
        WHERE   Outage_id = %s
        ORDER BY Recorded_at
    """, (outage_id,))

    summary = db.query("""
        SELECT  COUNT(*) AS Readings,
                ROUND(AVG(Temperature_c), 1) AS Avg_temp_c,
                MIN(Temperature_c) AS Min_temp_c,
                MAX(Wind_speed_kmh) AS Max_wind_kmh,
                SUM(Precip_mm) AS Total_precip_mm
        FROM    WEATHER_LOG
        WHERE   Outage_id = %s
    """, (outage_id,), one=True)

    return jsonify({"readings": readings, "summary": summary})


@api.route("/outages/<int:outage_id>/weather", methods=["POST"])
@role_required("admin", "user")
def record_outage_weather(outage_id):
    try:
        saved = weather.save_weather_for_outage(outage_id)
    except weather.WeatherError as e:
        return jsonify({"error": str(e)}), 502   # 502 = problem with an outside service
    return jsonify({"message": "Weather recorded at " + saved["station_name"] + ".", "reading": saved}), 201


# =====================================================================
# Chart data for the dashboard
# =====================================================================

@api.route("/charts", methods=["GET"])
@login_required
def chart_data():
    return jsonify({
        # View 10 from Phase II
        "backlog": db.query("""
            SELECT Priority, Open_jobs FROM BACKLOG_BY_PRIORITY
            ORDER BY CASE Priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2
                                   WHEN 'Medium' THEN 3 ELSE 4 END
        """),
        "by_status": db.query("""
            SELECT Status, COUNT(*) AS Total FROM WORK_ORDER GROUP BY Status ORDER BY Status
        """),
        # View 9 from Phase II
        "outages": db.query("""
            SELECT Station_name || ' U' || Unit_number AS Label, Planned_days, Actual_days
            FROM   OUTAGE_SUMMARY ORDER BY Start_date
        """),
    })
