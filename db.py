# db.py
# Helper functions for talking to the PostgreSQL database.
# Every query in the app goes through query() or execute(), so database
# errors are handled in one place.

import psycopg2
import psycopg2.extras
import config


class DatabaseError(Exception):
    """Raised when the database cannot be reached or a query fails."""
    pass


def get_connection():
    """Open a new connection to the database."""
    try:
        return psycopg2.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
        )
    except psycopg2.OperationalError as e:
        # Happens if PostgreSQL is not running or the login details are wrong
        raise DatabaseError("Could not connect to the database. Is PostgreSQL running? (" + str(e).strip() + ")")


def query(sql, params=None, one=False):
    """Run a SELECT and return the rows as a list of dictionaries.
    If one=True, return only the first row (or None)."""
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        if one:
            return rows[0] if rows else None
        return rows
    except psycopg2.Error as e:
        raise DatabaseError("Query failed: " + str(e).strip())
    finally:
        conn.close()


def execute(sql, params=None):
    """Run an INSERT, UPDATE or DELETE and save the change.
    Returns the number of rows affected."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        count = cur.rowcount
        conn.commit()
        cur.close()
        return count
    except psycopg2.Error as e:
        conn.rollback()      # undo the failed change
        raise DatabaseError("Update failed: " + str(e).strip())
    finally:
        conn.close()


def next_id(table, id_column):
    """Our tables use plain INT primary keys (no SERIAL), so we work out the
    next id ourselves. table and id_column are fixed names from our code,
    never user input."""
    row = query("SELECT COALESCE(MAX(" + id_column + "), 0) + 1 AS next FROM " + table, one=True)
    return row["next"]
