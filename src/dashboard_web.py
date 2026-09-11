from flask import Flask, render_template_string
import sqlite3

app = Flask(__name__)

DB_PATH = "data/sih.db"


HTML = '''
<!DOCTYPE html>
<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<meta http-equiv="refresh" content="5">

<title>SIH Meal Monitoring</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f4f6f8;
    color: #222;
}

.header {
    background: #17202a;
    color: white;
    padding: 22px;
}

.header h1 {
    margin: 0;
    font-size: 26px;
}

.header p {
    margin: 6px 0 0;
    opacity: 0.8;
}

.container {
    padding: 20px;
    max-width: 1100px;
    margin: auto;
}

.cards {
    display: grid;
    grid-template-columns:
    repeat(auto-fit, minmax(180px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
}

.card {
    background: white;
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.08);
}

.card h3 {
    margin: 0;
    font-size: 14px;
    color: #777;
}

.value {
    font-size: 30px;
    font-weight: bold;
    margin-top: 10px;
}

.section {
    background: white;
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 3px 10px rgba(0,0,0,0.08);
}

.section h2 {
    margin-top: 0;
}

.row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    padding: 14px 0;
    border-bottom: 1px solid #eee;
}

.row:last-child {
    border-bottom: none;
}

.label {
    color: #777;
}

.status {
    display: inline-block;
    padding: 8px 12px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 13px;
}

.ok {
    background: #d4edda;
    color: #155724;
}

.pending {
    background: #fff3cd;
    color: #856404;
}

.sync {
    background: #d1ecf1;
    color: #0c5460;
}

.refresh {
    text-align: center;
    margin-top: 15px;
    color: #888;
    font-size: 12px;
}

.footer {
    text-align: center;
    margin-top: 25px;
    color: #888;
    font-size: 13px;
}

</style>

</head>

<body>

<div class="header">

<h1>🍛 SIH Meal Monitoring</h1>

<p>
Intelligent Computer Vision System
</p>

</div>


<div class="container">


<div class="cards">


<div class="card">

<h3>Students Detected</h3>

<div class="value">
{{ person_count }}
</div>

</div>


<div class="card">

<h3>Plates Detected</h3>

<div class="value">
{{ plate_count }}
</div>

</div>


<div class="card">

<h3>Total Students</h3>

<div class="value">
{{ total_students }}
</div>

</div>


<div class="card">

<h3>Successful Meals</h3>

<div class="value">
{{ successful_meals }}
</div>

</div>


</div>


<div class="section">

<h2>Latest Monitoring</h2>


<div class="row">

<span class="label">
Scheduled Meal
</span>

<strong>
{{ scheduled_meal }}
</strong>

</div>


<div class="row">

<span class="label">
Meal Status
</span>

<span class="status
{% if meal_status == 'MEAL_OK' %}
ok
{% else %}
pending
{% endif %}
">

{{ meal_status }}

</span>

</div>


<div class="row">

<span class="label">
Sync Status
</span>

<span class="status sync">
{{ sync_status }}
</span>

</div>


<div class="row">

<span class="label">
Last Detection
</span>

<strong>
{{ timestamp }}
</strong>

</div>


</div>


<div class="refresh">

Dashboard automatically refreshes every 5 seconds.

</div>


<div class="footer">

SIH 2025 • Team NextGen •
Offline-first Meal Monitoring System

</div>


</div>

</body>

</html>
'''


def get_data():

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            timestamp,
            person_count,
            plate_count,
            scheduled_meal,
            meal_status,
            sync_status
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


    conn.close()


    if latest is None:

        return {
            "timestamp": "No data",
            "person_count": 0,
            "plate_count": "Pending",
            "scheduled_meal": "No data",
            "meal_status": "NO_DATA",
            "sync_status": "NO DATA",
            "total_students": 0,
            "successful_meals": 0
        }


    timestamp = latest[0]
    person_count = latest[1]
    plate_count = latest[2]
    scheduled_meal = latest[3]
    meal_status = latest[4]
    sync_value = latest[5]


    if plate_count is None:
        plate_count = "Pending"


    if sync_value == 1:
        sync_status = "SYNCED"
    else:
        sync_status = "PENDING SYNC"


    return {
        "timestamp": timestamp,
        "person_count": person_count,
        "plate_count": plate_count,
        "scheduled_meal": scheduled_meal,
        "meal_status": meal_status,
        "sync_status": sync_status,
        "total_students": total_students,
        "successful_meals": successful_meals
    }


@app.route("/")
def dashboard():

    data = get_data()

    return render_template_string(
        HTML,
        **data
    )


if __name__ == "__main__":

    print()
    print("====================================")
    print("       SIH WEB DASHBOARD")
    print("====================================")
    print()
    print("Open in browser:")
    print("http://127.0.0.1:5000")
    print()
    print("Dashboard refreshes every 5 seconds.")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )