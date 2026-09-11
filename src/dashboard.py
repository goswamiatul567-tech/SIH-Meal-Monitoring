import sqlite3


DB_PATH = "data/sih.db"


def get_dashboard_data():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Latest record
    cursor.execute("""
        SELECT
            id,
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


    # Total students detected
    cursor.execute("""
        SELECT COALESCE(SUM(person_count), 0)
        FROM meal_monitoring
    """)

    total_students = cursor.fetchone()[0]


    # Total plates detected
    cursor.execute("""
        SELECT COALESCE(SUM(plate_count), 0)
        FROM meal_monitoring
        WHERE plate_count IS NOT NULL
    """)

    total_plates = cursor.fetchone()[0]


    # Successful meals
    cursor.execute("""
        SELECT COUNT(*)
        FROM meal_monitoring
        WHERE meal_status = 'MEAL_OK'
    """)

    successful_meals = cursor.fetchone()[0]


    # Pending/incomplete meals
    cursor.execute("""
        SELECT COUNT(*)
        FROM meal_monitoring
        WHERE meal_status != 'MEAL_OK'
    """)

    pending_meals = cursor.fetchone()[0]


    # Synced records
    cursor.execute("""
        SELECT COUNT(*)
        FROM meal_monitoring
        WHERE sync_status = 1
    """)

    synced_records = cursor.fetchone()[0]


    conn.close()


    return (
        latest,
        total_students,
        total_plates,
        successful_meals,
        pending_meals,
        synced_records
    )


def show_dashboard():

    data = get_dashboard_data()

    (
        latest,
        total_students,
        total_plates,
        successful_meals,
        pending_meals,
        synced_records
    ) = data


    print()
    print("============================================")
    print("        SIH MEAL MONITORING DASHBOARD")
    print("============================================")


    if latest is None:

        print()
        print("No monitoring data available.")
        return


    (
        record_id,
        timestamp,
        person_count,
        plate_count,
        scheduled_meal,
        meal_status,
        sync_status
    ) = latest


    sync_text = (
        "SYNCED"
        if sync_status == 1
        else "PENDING SYNC"
    )


    print()
    print("------------- LATEST MONITORING -----------")

    print("Record ID        :", record_id)
    print("Timestamp        :", timestamp)
    print("Today's Meal     :", scheduled_meal)
    print("Students         :", person_count)
    print("Plates           :", plate_count)
    print("Meal Status      :", meal_status)
    print("Sync Status      :", sync_text)


    print()
    print("------------- OVERALL STATISTICS ----------")

    print("Total Students   :", total_students)
    print("Total Plates     :", total_plates)
    print("Successful Meals :", successful_meals)
    print("Pending/Other    :", pending_meals)
    print("Synced Records   :", synced_records)


    print()
    print("============================================")


if __name__ == "__main__":
    show_dashboard()