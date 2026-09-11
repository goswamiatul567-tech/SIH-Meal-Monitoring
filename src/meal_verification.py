def verify_meal(person_count, plate_count):
    """
    Basic meal verification.

    person_count = number of detected people
    plate_count = number of detected plates
    """

    if person_count == 0:
        return "NO_STUDENTS"

    if plate_count is None:
        return "PLATE_DETECTION_PENDING"

    if plate_count >= person_count:
        return "MEAL_OK"

    return "MEAL_INCOMPLETE"


if __name__ == "__main__":
    print(verify_meal(6, 6))
    print(verify_meal(6, 4))
    print(verify_meal(0, 0))