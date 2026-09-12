import os
import sqlite3
from flask import Flask, jsonify, render_template_string, request, send_file

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "sih.db")
LATEST_FRAME_PATH = os.path.join(BASE_DIR, "data", "latest_frame.jpg")

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


def get_dashboard_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT person_count, plate_count, scheduled_meal, meal_status, timestamp FROM meal_monitoring ORDER BY id DESC LIMIT 1")
    last_record = cursor.fetchone()

    cursor.execute("SELECT SUM(person_count) FROM meal_monitoring")
    total_students = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM meal_monitoring WHERE meal_status = 'MEAL_VERIFIED'")
    successful_meals = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM meal_monitoring WHERE sync_status = 0")
    pending_sync = cursor.fetchone()[0] or 0

    conn.close()

    if last_record:
        return {
            "students_detected": last_record[0],
            "plates_detected": last_record[1],
            "scheduled_meal": last_record[2],
            "meal_status": last_record[3],
            "last_detection": last_record[4],
            "total_students": total_students,
            "successful_meals": successful_meals,
            "pending_sync": pending_sync,
        }

    return {
        "students_detected": 0,
        "plates_detected": "Pending",
        "scheduled_meal": "Not specified",
        "meal_status": "NO DATA",
        "last_detection": "No detection yet",
        "total_students": 0,
        "successful_meals": 0,
        "pending_sync": 0,
    }


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SIH Meal Monitoring - Live Video</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b1120; color: #f8fafc; margin: 0; padding: 16px; }
        .header { text-align: center; margin-bottom: 20px; }
        .header h1 { margin: 0; font-size: 22px; color: #38bdf8; }
        .header p { margin: 4px 0 0 0; font-size: 12px; color: #94a3b8; }
        .container { max-width: 720px; margin: 0 auto; }
        
        .camera-card { background: #1e293b; border-radius: 12px; padding: 14px; margin-bottom: 20px; border: 1px solid #334155; text-align: center; }
        .camera-card h3 { margin: 0 0 10px 0; font-size: 13px; color: #38bdf8; text-transform: uppercase; text-align: left; letter-spacing: 0.5px; }
        
        /* Video Element for Smooth 30FPS stream */
        video#liveStream { width: 100%; max-height: 400px; border-radius: 8px; background: #020617; border: 1px solid #475569; transform: scaleX(1); }
        
        .controls { display: flex; gap: 10px; margin-top: 10px; }
        .btn-stream { flex: 1; background: #059669; color: white; border: none; padding: 10px; border-radius: 6px; font-weight: bold; cursor: pointer; }
        .btn-stop { flex: 1; background: #dc2626; color: white; border: none; padding: 10px; border-radius: 6px; font-weight: bold; cursor: pointer; }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 20px; margin-top: 20px; }
        .card { background: #1e293b; border-radius: 10px; padding: 14px; border: 1px solid #334155; }
        .card h4 { margin: 0 0 6px 0; font-size: 11px; color: #94a3b8; text-transform: uppercase; }
        .card p { margin: 0; font-size: 22px; font-weight: bold; color: #f8fafc; }
        
        .section { background: #1e293b; border-radius: 10px; padding: 14px; margin-bottom: 12px; border: 1px solid #334155; }
        .section-title { font-size: 11px; color: #94a3b8; text-transform: uppercase; margin-bottom: 4px; }
        .section-value { font-size: 16px; font-weight: 600; }
        
        .btn { display: block; width: 100%; text-align: center; background: #2563eb; color: white; padding: 12px; border-radius: 8px; font-size: 14px; font-weight: 600; border: none; cursor: pointer; text-decoration: none; margin-top: 16px; }
        .footer { text-align: center; margin-top: 24px; font-size: 11px; color: #64748b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SIH Meal Monitoring</h1>
            <p>Intelligent Computer Vision System for Mid-Day Meal Monitoring</p>
        </div>

        <!-- Real-time Live Video Stream Card -->
        <div class="camera-card">
            <h3>🔴 Real-Time Live Camera Feed</h3>
            <video id="liveStream" autoplay playsinline muted></video>
            <div class="controls">
                <button class="btn-stream" onclick="startCamera()">Turn On Camera</button>
                <button class="btn-stop" onclick="stopCamera()">Stop Camera</button>
            </div>
            <p id="camStatus" style="margin: 8px 0 0 0; font-size: 11px; color: #94a3b8;">Click 'Turn On Camera' to stream live video directly on website.</p>
        </div>

        <div class="grid">
            <div class="card">
                <h4>Students Detected</h4>
                <p>{{ data.students_detected }}</p>
            </div>
            <div class="card">
                <h4>Plates Detected</h4>
                <p>{{ data.plates_detected }}</p>
            </div>
            <div class="card">
                <h4>Total Students</h4>
                <p>{{ data.total_students }}</p>
            </div>
            <div class="card">
                <h4>Successful Meals</h4>
                <p>{{ data.successful_meals }}</p>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Today's Scheduled Meal</div>
            <div class="section-value">🍲 {{ data.scheduled_meal }}</div>
        </div>

        <div class="section">
            <div class="section-title">Meal Status</div>
            <div class="section-value" style="color: {% if data.meal_status == 'MEAL_VERIFIED' %}#4ade80{% else %}#f87171{% endif %};">
                {{ data.meal_status }}
            </div>
        </div>

        <div class="section">
            <div class="section-title">Last Detection Timestamp</div>
            <div class="section-value" style="font-size: 13px; color: #cbd5e1;">{{ data.last_detection }}</div>
        </div>

        <button class="btn" onclick="location.reload()">Refresh Data</button>

        <div class="footer">
            Atul Goswami<br>Edge AI Live Surveillance
        </div>
    </div>

    <script>
        let streamObj = null;

        async function startCamera() {
            const video = document.getElementById('liveStream');
            const status = document.getElementById('camStatus');
            try {
                // Constraints prioritize back camera for classroom monitoring
                const constraints = {
                    video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } }
                };
                streamObj = await navigator.mediaDevices.getUserMedia(constraints);
                video.srcObject = streamObj;
                status.innerText = "🟢 Camera live streaming smoothly (30 FPS)";
                status.style.color = "#4ade80";
            } catch (err) {
                // Fallback for front camera if back camera not directly accessible
                try {
                    streamObj = await navigator.mediaDevices.getUserMedia({ video: true });
                    video.srcObject = streamObj;
                    status.innerText = "🟢 Front camera live streaming";
                    status.style.color = "#4ade80";
                } catch (e) {
                    status.innerText = "❌ Permission denied or camera unavailable: " + e.message;
                    status.style.color = "#f87171";
                }
            }
        }

        function stopCamera() {
            if (streamObj) {
                streamObj.getTracks().forEach(track => track.stop());
                document.getElementById('liveStream').srcObject = null;
                document.getElementById('camStatus').innerText = "Camera stopped.";
                document.getElementById('camStatus').style.color = "#94a3b8";
            }
        }
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    data = get_dashboard_data()
    return render_template_string(HTML_TEMPLATE, data=data)


@app.route("/api/upload_frame", methods=["POST"])
def upload_frame():
    if "image" not in request.files:
        return jsonify({"status": "error", "message": "No image sent"}), 400
    file = request.files["image"]
    os.makedirs(os.path.dirname(LATEST_FRAME_PATH), exist_ok=True)
    file.save(LATEST_FRAME_PATH)
    return jsonify({"status": "success", "message": "Frame uploaded successfully"}), 200


@app.route("/api/latest_image")
def latest_image():
    if os.path.exists(LATEST_FRAME_PATH):
        return send_file(LATEST_FRAME_PATH, mimetype="image/jpeg")
    fallback = os.path.join(BASE_DIR, "outputs", "detected.jpg")
    if os.path.exists(fallback):
        return send_file(fallback, mimetype="image/jpeg")
    return jsonify({"status": "no image available"}), 404


@app.route("/api/sync", methods=["POST"])
def sync():
    records = request.get_json()
    if not records:
        return jsonify({"status": "error", "message": "No data received"}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for r in records:
        cursor.execute("""
            INSERT INTO meal_monitoring (timestamp, person_count, plate_count, scheduled_meal, meal_status, sync_status)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (r["timestamp"], r["person_count"], r["plate_count"], r["scheduled_meal"], r["meal_status"]))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "synced_records": len(records)}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
