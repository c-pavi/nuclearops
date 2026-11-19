# NuclearOps: Maintenance and Outage Tracker

SOFE 3700U Data Management Systems, Phase III

NuclearOps is a web application for tracking maintenance at nuclear generating
stations. Planners and technicians can manage work orders, equipment and workers,
run the 10 database views from Phase II, export reports, see charts, and record
weather during outages using an external weather API.

**Tech stack:** PostgreSQL, Python (Flask), HTML/CSS, JavaScript (Fetch API), Chart.js,
pandas (CSV export), fpdf2 (PDF export), Open-Meteo weather API.

---

## 1. What you need

| Software | Version | Download |
|---|---|---|
| Python | 3.10 or newer | https://www.python.org/downloads/ (on Windows, tick **"Add Python to PATH"** during install) |
| PostgreSQL + pgAdmin 4 | 16 or newer | https://www.postgresql.org/download/ |
| A web browser | any recent version | |

An internet connection is needed for the charts (Chart.js loads from a CDN) and for
the weather feature.

---

## 2. Install and run (Windows)

All commands are typed in **Command Prompt** inside the project folder.

### Step 1: Create the database
1. Open **pgAdmin 4** and connect to your PostgreSQL server.
2. Right-click **Databases > Create > Database**, name it `nuclearops`, and click **Save**.
   (If you already have it from Phase II, skip this step.)

### Step 2: Set your database password
Open `config.py` in a text editor and change `DB_PASSWORD` to the password you chose
when installing PostgreSQL:

```python
DB_PASSWORD = "your_postgres_password"
```

### Step 3: Install the Python packages
```
cd path\to\nuclearops
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4: Build the tables, sample data and views
```
python init_db.py
```
You should see:
```
Ran sql/schema.sql
Ran sql/sample_data.sql
Ran sql/views.sql
Demo passwords set. Database is ready.
```
Running this again resets the database back to the sample data.

### Step 5: Start the app
```
python app.py
```
Open **http://127.0.0.1:5000** in your browser. Press `Ctrl + C` in Command Prompt to stop it.

Next time, you only need:
```
cd path\to\nuclearops
venv\Scripts\activate
python app.py
```

### On Linux or macOS
Same steps, but activate the virtual environment with `source venv/bin/activate`
(and use `python3` if `python` is not found).

---

## 3. Demo accounts

| Username | Password | Role | What they can do |
|---|---|---|---|
| admin | admin123 | admin | Everything, including deleting records and managing equipment and workers |
| psharma | admin123 | admin | Same as admin (linked to worker Priya Sharma) |
| schen | user123 | user | View everything, create and edit work orders, record weather |
| dokafor | user123 | user | Same as schen |
| guest1 | guest123 | guest | View pages and reports only |

---

## 4. Pages

| Page | What it does |
|---|---|
| **Login** | Session-based login and logout |
| **Dashboard** | Summary counts and three Chart.js charts (backlog by priority, work orders by status, planned vs. actual outage length) |
| **Work Orders** | Search and filter by keyword, status, priority, station and due date. Create, edit and delete work orders without reloading the page. Picking equipment auto-fills its location and narrows the outage and worker lists to matching choices. |
| **Equipment** | Search, create, edit and delete equipment (admin) |
| **Workers** | Search, create, edit and delete workers (admin). Email is suggested from the name and checked as you type. |
| **Outage Weather** | Gets current weather at the station from the Open-Meteo API, saves it to `WEATHER_LOG`, and shows the history, a summary and a chart |
| **Reports** | Runs all 10 views from Phase II and shows the results as HTML tables, with CSV and PDF export |

---

## 5. How the project meets the Phase III requirements

| Requirement | Where it is |
|---|---|
| Login/logout with sessions | `app.py` (`login`, `logout`), Flask `session` |
| Roles (admin, user, guest) | `auth.py` (`login_required`, `role_required`) |
| Input validation | Server: `validation.py`. Browser: form checks in each `static/js/*.js` file |
| REST/JSON API (GET, POST, PUT, DELETE) | `api.py` |
| External API saved to the database | `weather.py` (Open-Meteo to `WEATHER_LOG`) |
| Web page using the external REST/JSON API + 2 queries | Outage Weather page. Queries: INSERT into `WEATHER_LOG`, SELECT readings, SELECT summary (AVG, MIN, MAX, SUM) |
| Web service that produces JSON and uses the database | Every `/api/...` endpoint in `api.py` |
| Full CRUD | Work orders, equipment and workers (`api.py`) |
| Export to CSV and PDF | `export.py` (pandas and fpdf2), buttons on each report page |
| Error handling | `db.py` (`DatabaseError`), `weather.py` (`WeatherError`), error handlers at the bottom of `app.py` |
| Two or more web pages | 8 pages in `templates/` |
| 10 views as HTML tables | Reports page (`report_view.html`) |
| Dynamic forms with validation and auto-fill | Work order form (equipment auto-fills location, outages and workers; status "Completed" fills today's date; title suggestions), worker form (email suggestion) |
| AJAX / Fetch API | `static/js/common.js` (`apiRequest`) used by every page |
| Charts (Chart.js) | Dashboard and Outage Weather pages |
| Search and filter | Work Orders, Equipment and Workers pages (filters run as SQL in `api.py`) |

---

## 6. REST API

All endpoints return JSON. You must be logged in.

| Method | URL | Who | Purpose |
|---|---|---|---|
| GET | `/api/work_orders?q=&status=&priority=&station_id=&due_from=&due_to=` | all | List with search and filters |
| GET | `/api/work_orders/<id>` | all | One work order |
| POST | `/api/work_orders` | admin, user | Create |
| PUT | `/api/work_orders/<id>` | admin, user | Update |
| DELETE | `/api/work_orders/<id>` | admin | Delete |
| GET / POST | `/api/equipment` | all / admin | List / create |
| GET / PUT / DELETE | `/api/equipment/<id>` | all / admin / admin | Read (includes outages and workers for auto-fill) / update / delete |
| GET / POST | `/api/workers` | all / admin | List / create |
| GET / PUT / DELETE | `/api/workers/<id>` | all / admin / admin | Read / update / delete |
| GET | `/api/outages/<id>/weather` | all | Saved weather and summary for an outage |
| POST | `/api/outages/<id>/weather` | admin, user | Get weather from Open-Meteo and save it |
| GET | `/api/stations`, `/api/systems`, `/api/outages` | all | Lists for dropdown menus |
| GET | `/api/charts` | all | Data for the dashboard charts |

Error responses look like `{"error": "...", "details": ["..."]}` with status
400 (bad input), 401 (not logged in), 403 (role not allowed), 404 (not found),
500 (database problem) or 502 (weather service problem).

---

## 7. Project structure

```
nuclearops/
  app.py            Main Flask app: pages, login, reports, export, error handlers
  api.py            REST/JSON API (CRUD, search, weather, chart data)
  auth.py           Login and role checks
  validation.py     Server-side input validation
  weather.py        Open-Meteo API call and saving to WEATHER_LOG
  export.py         CSV (pandas) and PDF (fpdf2) export
  db.py             Database connection and query helpers
  config.py         Database and app settings
  init_db.py        Builds the database from the SQL files
  requirements.txt  Python packages
  sql/              schema.sql, sample_data.sql, views.sql (from Phase II)
  templates/        HTML pages (Jinja templates)
  static/css/       style.css
  static/js/        JavaScript for each page
```

---

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| `Could not connect to the database` | Make sure PostgreSQL is running and the password in `config.py` is correct. |
| `database "nuclearops" does not exist` | Create it in pgAdmin (Step 1). |
| `'python' is not recognized` | Reinstall Python and tick "Add Python to PATH", or try `py` instead of `python`. |
| Charts do not appear | Chart.js loads from the internet; check your connection. |
| "Could not reach the weather service" | The weather feature needs internet access. The rest of the app still works. |
| Port 5000 already in use | Change the last line of `app.py` to `app.run(debug=True, port=5001)`. |

---

## 9. Notes

- Station names are real Canadian nuclear sites. All other data is made up for this project.
- Tables use plain `INT` primary keys (as in Phase II), so new IDs are worked out with `MAX(id) + 1`.
- All SQL uses parameters (`%s`) instead of pasting user input into the query, which prevents SQL injection.
- Passwords are stored as hashes using Werkzeug's `generate_password_hash`.
