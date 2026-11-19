# init_db.py
# Builds the database from scratch: tables, sample data, the 10 views,
# and real (hashed) passwords for the demo accounts.
#
# Run it once before starting the app:   python init_db.py
# WARNING: running it again deletes all data and starts over.

from werkzeug.security import generate_password_hash
import db

# Demo logins (username -> password). The sample data only has placeholder
# hashes, so we replace them with real hashes here.
DEMO_PASSWORDS = {
    "admin": "admin123",
    "psharma": "admin123",
    "schen": "user123",
    "dokafor": "user123",
    "lmurphy": "user123",
    "guest1": "guest123",
    "cnsc_viewer": "guest123",
}


def run_sql_file(path):
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
    print("Ran", path)


if __name__ == "__main__":
    run_sql_file("sql/schema.sql")
    run_sql_file("sql/sample_data.sql")
    run_sql_file("sql/views.sql")

    for username, password in DEMO_PASSWORDS.items():
        db.execute("UPDATE USER_ACCOUNT SET Password_hash = %s WHERE Username = %s",
                   (generate_password_hash(password), username))
    print("Demo passwords set. Database is ready.")
