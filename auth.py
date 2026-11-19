# auth.py
# Login checks and role-based access control.
#
# Roles:
#   guest - can only view pages and reports
#   user  - can also create and edit work orders and record weather
#   admin - can do everything, including deleting records and
#           managing equipment and workers

from functools import wraps
from flask import session, redirect, url_for, request, jsonify, flash


def is_api_request():
    return request.path.startswith("/api/")


def login_required(view_function):
    """Only let logged-in users see this page."""
    @wraps(view_function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            if is_api_request():
                return jsonify({"error": "You must be logged in."}), 401
            flash("Please log in first.")
            return redirect(url_for("login"))
        return view_function(*args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    """Only let users with one of the allowed roles use this page.
    Example: @role_required("admin", "user")"""
    def decorator(view_function):
        @wraps(view_function)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                if is_api_request():
                    return jsonify({"error": "You must be logged in."}), 401
                return redirect(url_for("login"))
            if session.get("role") not in allowed_roles:
                if is_api_request():
                    return jsonify({"error": "Your role (" + session.get("role") + ") is not allowed to do this."}), 403
                flash("Your role is not allowed to open that page.")
                return redirect(url_for("dashboard"))
            return view_function(*args, **kwargs)
        return wrapper
    return decorator
