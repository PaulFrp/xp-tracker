from datetime import datetime, timezone
import os

from flask import Blueprint, jsonify, render_template, request, session, redirect, url_for

from utils.db import get_db_connection

plants_bp = Blueprint("plants", __name__)


def _is_authorized_api_request():
    expected_key = os.getenv("PLANT_API_KEY", "")
    provided_key = request.headers.get("x-api-key", "")

    if not expected_key:
        return False, (jsonify({"error": "Server missing PLANT_API_KEY"}), 500)

    if provided_key != expected_key:
        return False, (jsonify({"error": "Unauthorized"}), 401)

    return True, None


@plants_bp.route("/api/sensor", methods=["POST"])
def receive_sensor_data():
    authorized, error_response = _is_authorized_api_request()
    if not authorized:
        return error_response

    payload = request.get_json(silent=True) or {}

    device_id = payload.get("device_id")
    moisture = payload.get("moisture")
    temperature = payload.get("temperature")
    humidity = payload.get("humidity")

    if not device_id:
        return jsonify({"error": "device_id is required"}), 400

    if moisture is None:
        return jsonify({"error": "moisture is required"}), 400

    try:
        moisture = float(moisture)
        temperature = float(temperature) if temperature is not None else None
        humidity = float(humidity) if humidity is not None else None
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid numeric values"}), 400

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO plant_sensor_readings (device_id, moisture, temperature, humidity)
            VALUES (%s, %s, %s, %s)
            """,
            (device_id, moisture, temperature, humidity),
        )

        # Ensure each device has a config row with default threshold.
        c.execute(
            """
            INSERT INTO plant_device_config (device_id)
            VALUES (%s)
            ON CONFLICT (device_id) DO NOTHING
            """,
            (device_id,),
        )

        conn.commit()

    return jsonify(
        {
            "status": "ok",
            "time": datetime.now(timezone.utc).isoformat(),
            "needs_water": moisture < 25,
        }
    )


@plants_bp.route("/plants", methods=["GET"])
def plants_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login.login"))

    with get_db_connection() as conn:
        c = conn.cursor()

        c.execute(
            """
            SELECT DISTINCT ON (r.device_id)
                r.device_id,
                COALESCE(cfg.display_name, r.device_id) AS display_name,
                r.moisture,
                r.temperature,
                r.humidity,
                COALESCE(cfg.moisture_threshold, 25) AS moisture_threshold,
                r.recorded_at
            FROM plant_sensor_readings r
            LEFT JOIN plant_device_config cfg ON cfg.device_id = r.device_id
            ORDER BY r.device_id, r.recorded_at DESC
            """
        )
        latest_readings = c.fetchall()

        c.execute(
            """
            SELECT device_id, moisture, temperature, humidity, recorded_at
            FROM plant_sensor_readings
            ORDER BY recorded_at DESC
            LIMIT 100
            """
        )
        recent_readings = c.fetchall()

    plants = []
    for row in latest_readings:
        device_id, display_name, moisture, temperature, humidity, threshold, recorded_at = row
        plants.append(
            {
                "device_id": device_id,
                "display_name": display_name,
                "moisture": moisture,
                "temperature": temperature,
                "humidity": humidity,
                "threshold": threshold,
                "needs_water": moisture is not None and moisture < threshold,
                "recorded_at": recorded_at,
            }
        )

    history = []
    for row in recent_readings:
        device_id, moisture, temperature, humidity, recorded_at = row
        history.append(
            {
                "device_id": device_id,
                "moisture": moisture,
                "temperature": temperature,
                "humidity": humidity,
                "recorded_at": recorded_at,
            }
        )

    return render_template("plants.html", plants=plants, history=history)
