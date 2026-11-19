# app.py
# Main file for the NuclearOps web app. Run it with:   python app.py
# Then open http://127.0.0.1:5000 in a browser.

from datetime import date, datetime
from decimal import Decimal

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, Response, abort)
from flask.json.provider import DefaultJSONProvider
from werkzeug.security import check_password_hash

import config
import db
import export
from api import api
from auth import login_required, role_required


# Flask's default JSON turns dates into long text like "Tue, 17 Nov 2026 00:00:00 GMT".
# This makes dates come out as "2026-11-17" (what HTML date inputs expect)
# and turns DECIMAL values into normal numbers.
class NuclearOpsJSON(DefaultJSONProvider):
    def default(self, value):
        if isinstance(value, (date, datetime)):
            return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return super().default(value)


app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.json = NuclearOpsJSON(app)
app.register_blueprint(api)


# The 10 views from Phase II. The key is the view's name in the database.
# Only names in this list can be shown or exported, which keeps users from
# sending their own SQL through the URL.
VIEWS = {
    "active_work_orders":          (1,  "Active Work Orders", "Open and in-progress work orders with their equipment and location.", "Due_date"),
    "busiest_workers":             (2,  "Busiest Workers", "The worker(s) with the most active work orders (uses >= ALL with GROUP BY).", "Worker_id"),
    "equipment_needing_attention": (3,  "Equipment Needing Attention", "Equipment whose latest inspection did not pass (correlated nested query).", "Equipment_id"),
    "worker_assignments":          (4,  "Worker Assignments", "All workers and all work orders, matched where possible (FULL JOIN).", "Worker_id, Work_order_id"),
    "available_workers":           (5,  "Available Workers", "Certified workers with no unfinished jobs (nested query with EXCEPT).", "Worker_id"),
    "overdue_inspections":         (6,  "Overdue Inspections", "Equipment past its inspection interval or never inspected.", "Next_due"),
    "low_stock_parts":             (7,  "Low Stock Parts", "Spare parts at or below their reorder level.", "Shortfall DESC"),
    "expiring_certifications":     (8,  "Expiring Certifications", "Workers whose certification has expired or expires within 60 days.", "Cert_expiry"),
    "outage_summary":              (9,  "Outage Summary", "Planned vs. actual length of completed outages.", "Start_date"),
    "backlog_by_priority":         (10, "Backlog by Priority", "Number of unfinished work orders at each priority.", "Open_jobs DESC"),
}


def get_view_rows(view_name):
    """Run SELECT * on one of our 10 views. Returns (info, rows)."""
    if view_name not in VIEWS:
        abort(404)
    info = VIEWS[view_name]
    # view_name and the ORDER BY both come from the VIEWS list above, not from the user
    rows = db.query("SELECT * FROM " + view_name + " ORDER BY " + info[3])
    return info, rows


# =====================================================================
# Login and logout
# =====================================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both a username and a password.")
            return render_template("login.html", username=username)

        user = db.query("SELECT * FROM USER_ACCOUNT WHERE Username = %s", (username,), one=True)
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Wrong username or password.")
            return render_template("login.html", username=username)

        # Save who is logged in. Flask signs this cookie so it cannot be changed by the user.
        session.clear()
        session["user_id"] = user["user_id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        session["worker_id"] = user["worker_id"]
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))


# =====================================================================
# Pages
# =====================================================================

@app.route("/")
@login_required
def dashboard():
    counts = db.query("""
        SELECT  (SELECT COUNT(*) FROM WORK_ORDER WHERE Status IN ('Open', 'In Progress')) AS Active_work_orders,
                (SELECT COUNT(*) FROM OVERDUE_INSPECTIONS) AS Overdue_inspections,
                (SELECT COUNT(*) FROM LOW_STOCK_PARTS) AS Low_stock_parts,
                (SELECT COUNT(*) FROM OUTAGE WHERE Status = 'In Progress') AS Outages_in_progress
    """, one=True)
    return render_template("dashboard.html", counts=counts)


@app.route("/work-orders")
@login_required
def work_orders_page():
    return render_template("work_orders.html")


@app.route("/equipment")
@login_required
def equipment_page():
    return render_template("equipment.html")


@app.route("/workers")
@login_required
def workers_page():
    return render_template("workers.html")


@app.route("/weather")
@login_required
def weather_page():
    return render_template("weather.html")


@app.route("/reports")
@login_required
def reports():
    return render_template("reports.html", views=VIEWS)


@app.route("/reports/<view_name>")
@login_required
def report_view(view_name):
    info, rows = get_view_rows(view_name)
    columns = list(rows[0].keys()) if rows else []
    return render_template("report_view.html", view_name=view_name, info=info,
                           rows=rows, columns=columns, views=VIEWS)


# =====================================================================
# Export to CSV and PDF
# =====================================================================

@app.route("/export/<view_name>.csv")
@login_required
def export_csv(view_name):
    info, rows = get_view_rows(view_name)
    return Response(export.to_csv(rows), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=" + view_name + ".csv"})


@app.route("/export/<view_name>.pdf")
@login_required
def export_pdf(view_name):
    info, rows = get_view_rows(view_name)
    return Response(export.to_pdf(info[1], rows), mimetype="application/pdf",
                    headers={"Content-Disposition": "attachment; filename=" + view_name + ".pdf"})


# =====================================================================
# Error handling
# =====================================================================

@app.errorhandler(db.DatabaseError)
def handle_database_error(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": str(e)}), 500
    return render_template("error.html", title="Database error", message=str(e)), 500


@app.errorhandler(404)
def handle_not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "That address does not exist."}), 404
    return render_template("error.html", title="Page not found",
                           message="The page you asked for does not exist."), 404


@app.errorhandler(405)
def handle_bad_method(e):
    return jsonify({"error": "That method is not allowed for this address."}), 405


@app.errorhandler(500)
def handle_server_error(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Something went wrong on the server."}), 500
    return render_template("error.html", title="Server error",
                           message="Something went wrong. Please try again."), 500


# Lets every template use the logged-in user's name and role
@app.context_processor
def add_user_to_templates():
    return {"current_user": session.get("username"), "current_role": session.get("role")}


if __name__ == "__main__":
    app.run(debug=True)
