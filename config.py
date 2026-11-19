# config.py
# Settings for the NuclearOps web app.
# Change these values to match your own PostgreSQL install.

DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "nuclearops"
DB_USER = "pavi"
DB_PASSWORD = ""

# Used by Flask to sign the session cookie. Any long random string works.
SECRET_KEY = "change-this-to-any-long-random-string"

# External weather API (Open-Meteo is free and does not need an API key)
WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
