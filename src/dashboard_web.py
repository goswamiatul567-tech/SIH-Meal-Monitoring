import os
import sqlite3
from flask import Flask, jsonify, render_template_string, request

# -------------------------------------------------
# Flask App
# -------------------------------------------------

app = Flask(__name__)

# -------------------------------------------------
# Database Setup
# -------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "sih.db")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meal_monitoring (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            person_count INTEGER NOT NULL,
            plate_count INTEGER,
            scheduled_meal TEXT,
            meal_status TEXT,
            sync_status INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


create_database()


# -------------------------------------------------
# Get Dashboard Data
# -------------------------------------------------

def get_data():
    create_database()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, person_count, plate_count, meal_status, scheduled_meal
        FROM meal_monitoring
        ORDER BY id DESC
        LIMIT 1
    """)
    latest = cursor.fetchone()

    cursor.execute("""
        SELECT COALESCE(SUM(person_count), 0)
        FROM meal_monitoring
    """)
    total_students = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM meal_monitoring
        WHERE meal_status = 'MEAL_OK'
    """)
    successful_meals = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM meal_monitoring
        WHERE sync_status = 0
    """)
    pending_sync = cursor.fetchone()[0]

    conn.close()

    if latest:
        timestamp = latest[0]
        person_count = latest[1]
        plate_count = latest[2]
        meal_status = latest[3]
        scheduled_meal = latest[4] if latest[4] else "Not specified"
    else:
        timestamp = "No detection yet"
        person_count = 0
        plate_count = None
        meal_status = "NO_DATA"
        scheduled_meal = "Not specified"

    return {
        "timestamp": timestamp,
        "person_count": person_count,
        "plate_count": plate_count,
        "total_students": total_students,
        "successful_meals": successful_meals,
        "meal_status": meal_status,
        "scheduled_meal": scheduled_meal,
        "pending_sync": pending_sync,
    }


# -------------------------------------------------
# Dashboard HTML
# -------------------------------------------------

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SIH Meal Monitoring</title>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f6f8;
            color: #222;
        }
        .header {
            background: #111827;
            color: white;
            padding: 22px;
            text-align: center;
        }
        .header h1 { margin: 0; font-size: 28px; }
        .header p { margin: 7px 0 0; opacity: 0.8; }
        .container {
            max-width: 1100px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
        }
        .card {
            background: white;
            border-radius: 14px;
            padding: 24px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }
        .card h3 { margin: 0 0 10px; color: #555; font-size: 15px; }
        .value { font-size: 32px; font-weight: bold; }
        .section { margin-top: 25px; }
        .status {
            padding: 18px;
            border-radius: 12px;
            background: white;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }
        .status h2 { margin-top: 0; }
        .info { margin: 10px 0; font-size: 17px; }
        .pending { color: #d97706; font-weight: bold; }
        .success { color: #16a34a; font-weight: bold; }
        .danger { color: #dc2626; font-weight: bold; }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #777;
            font-size: 14px;
        }
        .refresh {
            display: inline-block;
            margin-top: 15px;
            padding: 10px 18px;
            background: #2563eb;
            color: white;
            text-decoration: none;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>SIH Meal Monitoring</h1>
        <p>Intelligent Computer Vision System for Mid-Day Meal Monitoring</p>
    </div>
    <div class="container">
        <div class="grid">
            <div class="card">
                <h3>Students Detected</h3>
                <div class="value">{{ data.person_count }}</div>
            </div>
            <div class="card">
                <h3>Plates Detected</h3>
                <div class="value">
                    {% if data.plate_count is none %}
                        <span class="pending">Pending</span>
                    {% else %}
                        {{ data.plate_count }}
                    {% endif %}
                </div>
            </div>
            <div class="card">
                <h3>Total Students</h3>
                <div class="value">{{ data.total_students }}</div>
            </div>
            <div class="card">
                <h3>Successful Meals</h3>
                <div class="value">{{ data.successful_meals }}</div>
            </div>
        </div>

        <div class="section">
            <div class="status">
                <h2>Today's Scheduled Meal</h2>
                <div class="info">🍲 {{ data.scheduled_meal }}</div>
            </div>
        </div>

        <div class="section">
            <div class="status">
                <h2>Meal Status</h2>
                <div class="info">
                    {% if data.meal_status == "MEAL_OK" %}
                        <span class="success">✓ MEAL OK</span>
                    {% elif data.meal_status == "MEAL_INCOMPLETE" %}
                        <span class="danger">⚠ MEAL INCOMPLETE</span>
                    {% elif data.meal_status == "NO_STUDENTS" %}
                        <span class="danger">NO STUDENTS</span>
                    {% elif data.meal_status == "NO_DATA" %}
                        <span class="pending">NO DATA</span>
                    {% else %}
                        <span class="pending">{{ data.meal_status }}</span>
                    {% endif %}
                </div>
            </div>
        </div>

        <div class="section">
            <div class="status">
                <h2>Synchronization</h2>
                <div class="info">
                    {% if data.pending_sync > 0 %}
                        <span class="pending">{{ data.pending_sync }} record(s) pending sync</span>
                    {% else %}
                        <span class="success">✓ All records synced</span>
                    {% endif %}
                </div>
            </div>
        </div>

        <div class="section">
            <div class="status">
                <h2>Last Detection</h2>
                <div class="info">{{ data.timestamp }}</div>
                <a class="refresh" href="/">Refresh Dashboard</a>
            </div>
        </div>

        <div class="footer">
            Atul Goswami<br>
            Offline-first Meal Monitoring System
        </div>
    </div>
</body>
</html>
"""


# -------------------------------------------------
# Routes
# -------------------------------------------------

@app.route("/")
def dashboard():
    data = get_data()
    return render_template_string(HTML, data=data)


@app.route("/health")
def health():
    return {
        "status": "ok",
        "database": os.path.exists(DB_PATH),
    }


@app.route("/api/sync", methods=["POST"])
def sync_records():
    payload = request.get_json(silent=True)
    if not payload or "records" not in payload:
        return jsonify({"error": "Invalid payload, 'records' field required"}), 400

    records = payload["records"]
    if not isinstance(records, list):
        return jsonify({"error": "'records' must be a list"}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    synced_ids = []
    for r in records:
        cursor.execute("""
            INSERT INTO meal_monitoring (timestamp, person_count, plate_count, meal_status, scheduled_meal, sync_status)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (
            r.get("timestamp"),
            r.get("person_count"),
            r.get("plate_count"),
            r.get("meal_status"),
            r.get("scheduled_meal", "Not specified"),
        ))
        synced_ids.append(r.get("id"))

    conn.commit()
    conn.close()

    return jsonify({"status": "success", "synced_ids": synced_ids, "count": len(synced_ids)}), 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False,
    )
