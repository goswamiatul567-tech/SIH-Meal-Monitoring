from datetime import datetime


MEAL_SCHEDULE = {
    "Monday": "Rice, Dal, Vegetables",
    "Tuesday": "Roti, Dal, Vegetables",
    "Wednesday": "Rice, Dal, Vegetables",
    "Thursday": "Roti, Dal, Vegetables",
    "Friday": "Rice, Dal, Vegetables",
    "Saturday": "Khichdi, Vegetables",
}


def get_today_meal():
    today = datetime.now().strftime("%A")

    meal = MEAL_SCHEDULE.get(
        today,
        "No meal scheduled"
    )

    return today, meal


if __name__ == "__main__":
    day, meal = get_today_meal()

    print("Today:", day)
    print("Scheduled Meal:", meal)