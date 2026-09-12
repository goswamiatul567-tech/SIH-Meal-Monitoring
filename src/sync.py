import os
import sqlite3
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "sih.db")
OUTPUT_IMAGE = os.path.join(BASE_DIR, "outputs", "detected.jpg")

CLOUD_SYNC_URL = "https://sih-meal-monitoring.onrender.com/api/sync"
CLOUD_IMAGE_URL = "https://sih-meal-monitoring.onrender.com/api/upload_frame"


def sync_data():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, timestamp, person_count, plate_count, scheduled_meal, meal_status FROM meal_monitoring WHERE sync_status = 0")
    rows = cur.fetchall()

    if rows:
        payload = []
        ids = []
        for r in rows:
            ids.append(r[0])
            payload.append({
                "timestamp": r[1],
                "person_count": r[2],
                "plate_count": r[3],
                "scheduled_meal": r[4],
                "meal_status": r[5]
            })

        try:
            res = requests.post(CLOUD_SYNC_URL, json=payload, timeout=10)
            if res.status_code == 200:
                placeholders = ",".join("?" * len(ids))
                cur.execute(f"UPDATE meal_monitoring SET sync_status = 1 WHERE id IN ({placeholders})", ids)
                conn.commit()
                print(f"Successfully synced {len(ids)} record(s) to Cloud!")
            else:
                print(f"Sync failed: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"Network error during database sync: {e}")
    else:
        print("No pending database records to sync.")

    conn.close()

    # Upload latest live camera frame to website
    if os.path.exists(OUTPUT_IMAGE):
        try:
            print("Uploading latest camera visual frame to website...")
            with open(OUTPUT_IMAGE, "rb") as img_file:
                res = requests.post(CLOUD_IMAGE_URL, files={"image": img_file}, timeout=15)
                if res.status_code == 200:
                    print("Camera feed successfully pushed to Cloud Dashboard!")
                else:
                    print(f"Image upload status: {res.status_code}")
        except Exception as e:
            print(f"Could not upload visual frame: {e}")
    else:
        print(f"No output image found at {OUTPUT_IMAGE}")


if __name__ == "__main__":
    sync_data()
