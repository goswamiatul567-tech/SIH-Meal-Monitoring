import sqlite3
import requests

DB_PATH = "data/sih.db"
CLOUD_SYNC_URL = "https://sih-meal-monitoring.onrender.com/api/sync"


def get_unsynced_records():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, timestamp, person_count, plate_count, meal_status, scheduled_meal
        FROM meal_monitoring
        WHERE sync_status = 0
    """)

    rows = cursor.fetchall()
    conn.close()

    records = []
    for r in rows:
        records.append({
            "id": r[0],
            "timestamp": r[1],
            "person_count": r[2],
            "plate_count": r[3],
            "meal_status": r[4],
            "scheduled_meal": r[5]
        })

    return records


def mark_as_synced(record_ids):
    if not record_ids:
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for rec_id in record_ids:
        cursor.execute("""
            UPDATE meal_monitoring
            SET sync_status = 1
            WHERE id = ?
        """, (rec_id,))

    conn.commit()
    conn.close()


def sync_to_cloud():
    records = get_unsynced_records()
    total = len(records)

    print(f"Unsynced records found: {total}")

    if total == 0:
        print("Everything is already synced with cloud.")
        return

    print("Sending records to Render cloud...")

    try:
        response = requests.post(
            CLOUD_SYNC_URL,
            json={"records": records},
            timeout=15
        )

        if response.status_code == 200:
            result = response.json()
            synced_ids = result.get("synced_ids", [])
            mark_as_synced(synced_ids)
            print(f"Successfully synced {len(synced_ids)} records to cloud!")
        else:
            print(f"Failed to sync. Server returned status {response.status_code}: {response.text}")

    except Exception as e:
        print("Sync failed (offline or network error):", e)


if __name__ == "__main__":
    sync_to_cloud()
