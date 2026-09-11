import sqlite3
from datetime import datetime

DB_PATH = "data/sih.db"


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

    print("Database ready!")


def save_record(
    person_count,
    plate_count=None,
    scheduled_meal="Not specified",
    meal_status="OK"
):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO meal_monitoring
        (
            timestamp,
            person_count,
            plate_count,
            scheduled_meal,
            meal_status
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        person_count,
        plate_count,
        scheduled_meal,
        meal_status
    ))

    conn.commit()
    conn.close()

    print("Record saved!")


if __name__ == "__main__":
    create_database()