import sqlite3

DB_PATH = "data/sih.db"


def get_unsynced_records():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, timestamp, person_count, plate_count, meal_status
        FROM meal_monitoring
        WHERE sync_status = 0
    """)

    records = cursor.fetchall()

    conn.close()

    return records


def mark_as_synced(record_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE meal_monitoring
        SET sync_status = 1
        WHERE id = ?
    """, (record_id,))

    conn.commit()
    conn.close()


def show_unsynced_records():
    records = get_unsynced_records()

    print("Unsynced records:", len(records))

    for record in records:
        print(record)


if __name__ == "__main__":
    show_unsynced_records()