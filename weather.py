# weather.py
# Gets current weather from the Open-Meteo API (an external REST/JSON service)
# and saves it to the WEATHER_LOG table.

import requests
import config
import db


class WeatherError(Exception):
    """Raised when the weather API cannot be reached or sends back bad data."""
    pass


# Open-Meteo returns a number code for the weather. We turn it into a short word.
WEATHER_CODES = {
    0: "Clear", 1: "Mostly Clear", 2: "Partly Cloudy", 3: "Cloudy",
    45: "Fog", 48: "Fog",
    51: "Drizzle", 53: "Drizzle", 55: "Drizzle",
    61: "Rain", 63: "Rain", 65: "Heavy Rain",
    66: "Freezing Rain", 67: "Freezing Rain",
    71: "Snow", 73: "Snow", 75: "Heavy Snow", 77: "Snow",
    80: "Showers", 81: "Showers", 82: "Heavy Showers",
    85: "Snow Showers", 86: "Snow Showers",
    95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm",
}


def fetch_current_weather(latitude, longitude):
    """Call the Open-Meteo API and return the current weather as a dictionary."""
    params = {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "current": "temperature_2m,wind_speed_10m,precipitation,weather_code",
        "timezone": "auto",           # times come back in the station's local time
    }
    try:
        response = requests.get(config.WEATHER_API_URL, params=params, timeout=10)
        response.raise_for_status()   # raises an error for 4xx/5xx responses
        data = response.json()
    except requests.exceptions.Timeout:
        raise WeatherError("The weather service took too long to respond. Please try again.")
    except requests.exceptions.RequestException as e:
        print("Weather API error:", e)     # full details go to the server console for debugging
        raise WeatherError("Could not reach the weather service. Check your internet connection and try again.")
    except ValueError:
        raise WeatherError("The weather service sent back data that is not valid JSON.")

    current = data.get("current")
    if not current or "temperature_2m" not in current:
        raise WeatherError("The weather service response was missing the current weather.")

    return {
        "recorded_at": current["time"].replace("T", " ") + ":00",
        "temperature_c": current["temperature_2m"],
        "wind_speed_kmh": current["wind_speed_10m"],
        "precip_mm": current.get("precipitation", 0) or 0,
        "conditions": WEATHER_CODES.get(current.get("weather_code"), "Unknown"),
    }


def save_weather_for_outage(outage_id):
    """Look up the outage's station location, get the weather there,
    and save it as a new row in WEATHER_LOG. Returns the saved row."""

    # Query 1: find the station's coordinates for this outage
    location = db.query("""
        SELECT  S.Name AS Station_name, S.Latitude, S.Longitude
        FROM    OUTAGE AS O
            JOIN REACTOR_UNIT AS R  ON O.Unit_id = R.Unit_id
            JOIN STATION AS S       ON R.Station_id = S.Station_id
        WHERE   O.Outage_id = %s
    """, (outage_id,), one=True)
    if location is None:
        raise WeatherError("Outage " + str(outage_id) + " does not exist.")

    weather = fetch_current_weather(location["latitude"], location["longitude"])

    # Query 2: save the weather reading into our database
    weather_id = db.next_id("WEATHER_LOG", "Weather_id")
    db.execute("""
        INSERT INTO WEATHER_LOG (Weather_id, Outage_id, Recorded_at, Temperature_c,
                                 Wind_speed_kmh, Precip_mm, Conditions)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (weather_id, outage_id, weather["recorded_at"], weather["temperature_c"],
          weather["wind_speed_kmh"], weather["precip_mm"], weather["conditions"]))

    weather["weather_id"] = weather_id
    weather["station_name"] = location["station_name"]
    return weather
