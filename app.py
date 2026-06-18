import os
import requests
import datetime
import pytz
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# OSRM and Nominatim base URLs (Free, no API keys needed)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "http://router.project-osrm.org/route/v1/driving"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# Geocode addresses inside Santiago de Chile
def geocode_address(address):
    headers = {
        "User-Agent": "SantiagoTariffComparer/1.0 (contact: support@comparer.cl)"
    }
    # Append "Santiago, Chile" to restrict queries
    query = f"{address}, Santiago, Chile"
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "addressdetails": 1
    }
    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        if response.status_code == 200 and len(response.json()) > 0:
            data = response.json()[0]
            return {
                "display_name": data["display_name"],
                "lat": float(data["lat"]),
                "lon": float(data["lon"])
            }
    except Exception as e:
        print(f"Geocoding error for {address}: {e}")
    return None

# Get route distance (meters) and duration (seconds)
def get_route(start_coords, end_coords):
    url = f"{OSRM_URL}/{start_coords['lon']},{start_coords['lat']};{end_coords['lon']},{end_coords['lat']}"
    params = {
        "overview": "full",
        "geometries": "geojson"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "routes" in data and len(data["routes"]) > 0:
                route = data["routes"][0]
                return {
                    "distance_km": route["distance"] / 1000.0,
                    "duration_mins": route["duration"] / 60.0,
                    "geometry": route["geometry"]
                }
    except Exception as e:
        print(f"Routing error: {e}")
    return None

# Fetch current weather code for Santiago to determine if it is raining
def get_santiago_weather():
    params = {
        "latitude": -33.4489,
        "longitude": -70.6693,
        "current": "weather_code"
    }
    try:
        response = requests.get(WEATHER_URL, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            weather_code = data.get("current", {}).get("weather_code", 0)
            # Weather codes >= 50 typically represent rain/drizzle/snow/thunderstorms
            is_raining = weather_code >= 50
            return {
                "is_raining": is_raining,
                "code": weather_code
            }
    except Exception as e:
        print(f"Weather API error: {e}")
    return {"is_raining": False, "code": 0}

# Tariff computation details in Chilean Pesos (CLP)
def calculate_tariffs(distance_km, duration_mins):
    # 1. Fetch current weather for Santiago Centro
    weather_info = get_santiago_weather()
    is_raining = weather_info["is_raining"]

    # 2. Get local time in Santiago de Chile
    santiago_tz = pytz.timezone("America/Santiago")
    now_santiago = datetime.datetime.now(santiago_tz)
    current_time = now_santiago.time()

    # Determine dynamic surge multipliers
    surge_multiplier = 1.0
    reason_tags = []

    # Rush hour windows (Monday - Friday)
    is_weekday = now_santiago.weekday() < 5
    if is_weekday:
        # Morning rush: 7:30 to 9:30
        if datetime.time(7, 30) <= current_time <= datetime.time(9, 30):
            surge_multiplier += 0.45
            reason_tags.append("Morning Rush Hour")
        # Evening rush: 17:30 to 20:00
        elif datetime.time(17, 30) <= current_time <= datetime.time(20, 0):
            surge_multiplier += 0.55
            reason_tags.append("Evening Rush Hour")

    # Late night surge (23:00 to 05:00)
    if current_time >= datetime.time(23, 0) or current_time <= datetime.time(5, 0):
        surge_multiplier += 0.3
        reason_tags.append("Night/Late Hours")

    # Weather surge (Rain)
    if is_raining:
        surge_multiplier += 0.4
        reason_tags.append("Precipitation (Rain)")

    # Base pricing formulas in Santiago
    # UberX
    uber_x_base = 700
    uber_x_km = 250
    uber_x_min = 120
    uber_x_min_fare = 1400
    uber_x_calc = (uber_x_base + (distance_km * uber_x_km) + (duration_mins * uber_x_min)) * surge_multiplier
    uber_x_final = max(uber_x_min_fare, int(uber_x_calc))

    # Uber Comfort
    uber_c_base = 1000
    uber_c_km = 320
    uber_c_min = 150
    uber_c_min_fare = 2000
    uber_c_calc = (uber_c_base + (distance_km * uber_c_km) + (duration_mins * uber_c_min)) * surge_multiplier
    uber_c_final = max(uber_c_min_fare, int(uber_c_calc))

    # DiDi Express
    didi_e_base = 600
    didi_e_km = 220
    didi_e_min = 100
    didi_e_min_fare = 1200
    didi_e_calc = (didi_e_base + (distance_km * didi_e_km) + (duration_mins * didi_e_min)) * surge_multiplier
    didi_e_final = max(didi_e_min_fare, int(didi_e_calc))

    # DiDi Taxi
    didi_t_base = 800
    didi_t_km = 260
    didi_t_min = 130
    didi_t_min_fare = 1500
    didi_t_calc = (didi_t_base + (distance_km * didi_t_km) + (duration_mins * didi_t_min)) * surge_multiplier
    didi_t_final = max(didi_t_min_fare, int(didi_t_calc))

    if not reason_tags:
        reason_tags.append("Normal Demand")

    return {
        "surge_factor": round(surge_multiplier, 2),
        "reasons": ", ".join(reason_tags),
        "is_raining": is_raining,
        "local_time": now_santiago.strftime("%H:%M"),
        "uber": {
            "uberx": uber_x_final,
            "comfort": uber_c_final
        },
        "didi": {
            "express": didi_e_final,
            "taxi": didi_t_final
        }
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/compare", methods=["POST"])
def compare():
    req_data = request.json or {}
    start_addr = req_data.get("start")
    end_addr = req_data.get("end")

    if not start_addr or not end_addr:
        return jsonify({"error": "Both starting point and destination are required"}), 400

    # 1. Geocode Start & End
    start_coords = geocode_address(start_addr)
    if not start_coords:
        return jsonify({"error": f"Could not find coordinates for starting address: '{start_addr}' in Santiago"}), 400

    end_coords = geocode_address(end_addr)
    if not end_coords:
        return jsonify({"error": f"Could not find coordinates for destination address: '{end_addr}' in Santiago"}), 400

    # 2. Get Route
    route_details = get_route(start_coords, end_coords)
    if not route_details:
        return jsonify({"error": "Could not calculate a driving route between these locations"}), 400

    # 3. Calculate Tariffs
    tariffs = calculate_tariffs(
        route_details["distance_km"],
        route_details["duration_mins"]
    )

    return jsonify({
        "start": start_coords,
        "end": end_coords,
        "distance_km": round(route_details["distance_km"], 2),
        "duration_mins": round(route_details["duration_mins"], 1),
        "geometry": route_details["geometry"],
        "tariffs": tariffs
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
