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

    # Fetch last 5 audit logs
    cursor.execute("SELECT id, timestamp, person_count, plate_count, scheduled_meal, meal_status, sync_status FROM meal_monitoring ORDER BY id DESC LIMIT 5")
    recent_logs = cursor.fetchall()

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
            "recent_logs": recent_logs,
        }

    return {
        "students_detected": 0,
        "plates_detected": 0,
        "scheduled_meal": "Not specified",
        "meal_status": "AWAITING DATA",
        "last_detection": "No detection yet",
        "total_students": 0,
        "successful_meals": 0,
        "recent_logs": [],
    }


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Atul's Meal Monitoring System</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', -apple-system, sans-serif; background: #090d16; color: #f1f5f9; min-height: 100vh; padding: 20px 16px; }
        
        /* Top Navigation Header */
        .header-bar {
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 14px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1100px;
            margin: 0 auto 20px auto;
        }
        .header-title { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 16px; letter-spacing: 0.5px; color: #f8fafc; }
        .live-dot { width: 10px; height: 10px; background: #ef4444; border-radius: 50%; box-shadow: 0 0 10px #ef4444; animation: pulse 1.8s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.85); } }
        .header-meta { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #94a3b8; }
        .badge-active { background: rgba(16, 185, 129, 0.15); color: #34d399; padding: 3px 8px; border-radius: 4px; border: 1px solid rgba(16, 185, 129, 0.3); }

        /* Main Workspace Split Grid */
        .workspace {
            display: grid;
            grid-template-columns: 1.4fr 1fr;
            gap: 20px;
            max-width: 1100px;
            margin: 0 auto 20px auto;
        }
        @media (max-width: 850px) { .workspace { grid-template-columns: 1fr; } }

        /* Left Surveillance Panel */
        .panel {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 18px;
            display: flex;
            flex-direction: column;
        }
        .panel-header {
            font-size: 11px;
            font-family: 'JetBrains Mono', monospace;
            text-transform: uppercase;
            color: #38bdf8;
            letter-spacing: 1px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
        }
        .video-container {
            position: relative;
            background: #020617;
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid #1e293b;
            aspect-ratio: 16/9;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        video#liveStream { width: 100%; height: 100%; object-fit: cover; }
        .hud-overlay {
            position: absolute;
            top: 10px;
            left: 10px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            background: rgba(0, 0, 0, 0.65);
            padding: 4px 8px;
            border-radius: 4px;
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }

        .controls { display: flex; gap: 10px; margin-top: 14px; }
        .btn-stream {
            flex: 1;
            background: #10b981;
            color: #042f2e;
            font-weight: 700;
            font-size: 13px;
            padding: 10px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            transition: 0.2s;
        }
        .btn-stream:hover { background: #34d399; }
        .btn-stop {
            flex: 1;
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            font-weight: 700;
            font-size: 13px;
            padding: 10px;
            border-radius: 6px;
            border: 1px solid rgba(239, 68, 68, 0.3);
            cursor: pointer;
        }
        .status-txt { font-size: 11px; color: #94a3b8; font-family: 'JetBrains Mono', monospace; margin-top: 8px; text-align: center; }

        /* Right Telemetry Panel */
        .telemetry-grid { display: flex; flex-direction: column; gap: 12px; }
        .metric-card {
            background: rgba(30, 41, 59, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 14px 16px;
        }
        .metric-label { font-size: 11px; text-transform: uppercase; color: #94a3b8; font-family: 'JetBrains Mono', monospace; margin-bottom: 4px; }
        .metric-val { font-size: 24px; font-weight: 700; color: #f8fafc; }
        .metric-sub { font-size: 11px; color: #64748b; margin-top: 2px; }

        .metric-status {
            font-size: 16px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            color: {% if data.meal_status == 'MEAL_VERIFIED' %}#34d399{% else %}#f87171{% endif %};
        }

        /* Bottom Audit Log Timeline */
        .audit-panel {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 18px;
            max-width: 1100px;
            margin: 0 auto;
        }
        .table-wrap { overflow-x: auto; margin-top: 10px; }
        table { width: 100%; border-collapse: collapse; font-family: 'JetBrains Mono', monospace; font-size: 12px; text-align: left; }
        th { color: #64748b; font-weight: 600; padding: 10px 8px; border-bottom: 1px solid #1e293b; text-transform: uppercase; font-size: 11px; }
        td { padding: 10px 8px; border-bottom: 1px solid rgba(30, 41, 59, 0.5); color: #cbd5e1; }
        .tag-sync { color: #34d399; background: rgba(16, 185, 129, 0.1); padding: 2px 6px; border-radius: 4px; }
    </style>
</head>
<body>

    <!-- Header -->
    <div class="header-bar">
        <div class="header-title">
            <div class="live-dot"></div>
            ATUL'S MEAL MONITORING SYSTEM
        </div>
        <div class="header-meta">
            STATUS: <span class="badge-active">ONLINE</span> &nbsp;|&nbsp; UNIT #01
        </div>
    </div>

    <!-- Main Section: Stream (Left) + Telemetry (Right) -->
    <div class="workspace">
        
        <!-- Live Surveillance -->
        <div class="panel">
            <div class="panel-header">
                <span>LIVE SURVEILLANCE FEED</span>
                <span style="color: #94a3b8;">WEBCAM 30 FPS</span>
            </div>
            <div class="video-container">
                <video id="liveStream" autoplay playsinline muted></video>
                <div class="hud-overlay" id="hudTag">STREAM OFFLINE</div>
            </div>
            <div class="controls">
                <button class="btn-stream" onclick="startCamera()">START STREAM</button>
                <button class="btn-stop" onclick="stopCamera()">STOP</button>
            </div>
            <div class="status-txt" id="camStatus">Click 'START STREAM' to broadcast live video feed</div>
        </div>

        <!-- Real-Time Telemetry -->
        <div class="panel">
            <div class="panel-header">
                <span>REAL-TIME TELEMETRY</span>
                <span style="color: #94a3b8;">AUTO-REFRESH</span>
            </div>
            <div class="telemetry-grid">
                <div class="metric-card">
                    <div class="metric-label">Students Active / Concurrent</div>
                    <div class="metric-val">{{ data.students_detected }}</div>
                    <div class="metric-sub">Cumulative logged: {{ data.total_students }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Plates Monitored</div>
                    <div class="metric-val">{{ data.plates_detected }}</div>
                    <div class="metric-sub">Served count verification</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Scheduled Menu (Today)</div>
                    <div class="metric-val" style="font-size: 18px;">🍲 {{ data.scheduled_meal }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Meal Integrity State</div>
                    <div class="metric-status">{{ data.meal_status }}</div>
                </div>
            </div>
        </div>

    </div>

    <!-- Recent Audit Logs Timeline -->
    <div class="audit-panel">
        <div class="panel-header">
            <span>RECENT AUDIT LOG TIMELINE (SQLITE SYNC ENGINE)</span>
            <span style="cursor: pointer; color: #38bdf8;" onclick="location.reload()">[REFRESH]</span>
        </div>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Timestamp</th>
                        <th>Students</th>
                        <th>Plates</th>
                        <th>Integrity</th>
                        <th>Sync Engine</th>
                    </tr>
                </thead>
                <tbody>
                    {% for log in data.recent_logs %}
                    <tr>
                        <td>#{{ log[0] }}</td>
                        <td>{{ log[1] }}</td>
                        <td>{{ log[2] }}</td>
                        <td>{{ log[3] }}</td>
                        <td>{{ log[5] }}</td>
                        <td><span class="tag-sync">Synced ✓</span></td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="6" style="text-align: center; color: #64748b; padding: 18px;">No audit records captured yet.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        let streamObj = null;

        async function startCamera() {
            const video = document.getElementById('liveStream');
            const hud = document.getElementById('hudTag');
            const status = document.getElementById('camStatus');
            try {
                const constraints = {
                    video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } }
                };
                streamObj = await navigator.mediaDevices.getUserMedia(constraints);
                video.srcObject = streamObj;
                hud.innerText = "● LIVE (30 FPS)";
                hud.style.color = "#34d399";
                hud.style.borderColor = "rgba(52, 211, 153, 0.4)";
                status.innerText = "Camera stream connected successfully.";
                status.style.color = "#34d399";
            } catch (err) {
                try {
                    streamObj = await navigator.mediaDevices.getUserMedia({ video: true });
                    video.srcObject = streamObj;
                    hud.innerText = "● LIVE (FRONT CAM)";
                    status.innerText = "Front webcam connected.";
                    status.style.color = "#34d399";
                } catch (e) {
                    status.innerText = "Permission denied or no camera device found.";
                    status.style.color = "#f87171";
                }
            }
        }

        function stopCamera() {
            if (streamObj) {
                streamObj.getTracks().forEach(track => track.stop());
                document.getElementById('liveStream').srcObject = null;
                document.getElementById('hudTag').innerText = "STREAM OFFLINE";
                document.getElementById('hudTag').style.color = "#38bdf8";
                document.getElementById('camStatus').innerText = "Camera feed terminated.";
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
