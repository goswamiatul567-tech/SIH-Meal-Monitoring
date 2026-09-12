import os
import subprocess
import time
import cv2
import numpy as np
import onnxruntime as ort

from database import save_record
from meal_schedule import get_today_meal
from meal_verification import verify_meal
from plate_detector import detect_plates

PERSON_MODEL = "models/yolov8n.onnx"
LIVE_IMAGE = "images/live.jpg"
OUTPUT_PATH = "outputs/detected.jpg"

INPUT_SIZE = 640
CONF_THRESHOLD = 0.40
NMS_THRESHOLD = 0.45
CAPTURE_INTERVAL_SECONDS = 6  # Interval between live scans

def capture_photo():
    if os.path.exists(LIVE_IMAGE):
        try:
            os.remove(LIVE_IMAGE)
        except OSError:
            pass
    cmd = ["termux-camera-photo", "-c", "0", LIVE_IMAGE]
    subprocess.run(cmd, capture_output=True, text=True)
    time.sleep(1)
    return os.path.exists(LIVE_IMAGE) and os.path.getsize(LIVE_IMAGE) > 0

def detect_persons(image, session, input_name):
    original_h, original_w = image.shape[:2]
    img = cv2.resize(image, (INPUT_SIZE, INPUT_SIZE))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)

    output = session.run(None, {input_name: img})[0]
    predictions = output[0].T

    boxes = []
    scores = []
    for pred in predictions:
        confidence = float(pred[4])
        if confidence < CONF_THRESHOLD:
            continue
        cx, cy, bw, bh = pred[:4]
        x1 = int((cx - bw / 2) * original_w / INPUT_SIZE)
        y1 = int((cy - bh / 2) * original_h / INPUT_SIZE)
        box_w = int(bw * original_w / INPUT_SIZE)
        box_h = int(bh * original_h / INPUT_SIZE)
        boxes.append([x1, y1, box_w, box_h])
        scores.append(confidence)

    if not boxes:
        return []
    indices = cv2.dnn.NMSBoxes(boxes, scores, CONF_THRESHOLD, NMS_THRESHOLD)
    return [{"box": boxes[int(i)], "confidence": scores[int(i)]} for i in indices]

def run_continuous_monitor():
    print("==================================================")
    print("  LIVE CONTINUOUS MID-DAY MEAL SURVEILLANCE")
    print(f"  Scan interval: Every {CAPTURE_INTERVAL_SECONDS} seconds")
    print("  Press CTRL+C in Termux to stop monitoring.")
    print("==================================================")

    day_name, scheduled_meal = get_today_meal()
    print(f"Scheduled Meal: {scheduled_meal} ({day_name})\n")

    print("Initializing YOLOv8 Engine...")
    person_session = ort.InferenceSession(PERSON_MODEL)
    person_input = person_session.get_inputs()[0].name

    iteration = 1
    max_students_seen = 0
    total_plates_served = 0

    try:
        while True:
            print(f"\n[Scan #{iteration}] Capturing frame...")
            if not capture_photo():
                print("Camera capture failed, retrying in 3 seconds...")
                time.sleep(3)
                continue

            image = cv2.imread(LIVE_IMAGE)
            if image is None:
                continue

            # Run Inferences
            person_results = detect_persons(image, person_session, person_input)
            student_count = len(person_results)

            plate_count, plate_results = detect_plates(image)

            # Verification Logic
            meal_status = verify_meal(student_count, plate_count)

            # Session tracker updates
            if student_count > max_students_seen:
                max_students_seen = student_count
            
            # Simple heuristic: tracking verified servings
            if plate_count > total_plates_served:
                total_plates_served = plate_count

            # Log to DB
            save_record(
                person_count=student_count,
                plate_count=plate_count,
                scheduled_meal=scheduled_meal,
                meal_status=meal_status,
            )

            # Terminal Report
            print(f"-> Active Students : {student_count} (Peak: {max_students_seen})")
            print(f"-> Plates Detected : {plate_count} (Verified Served: {total_plates_served})")
            print(f"-> Verification    : {meal_status}")
            print(f"-> Record logged in sih.db. Next scan in {CAPTURE_INTERVAL_SECONDS}s...")

            iteration += 1
            time.sleep(CAPTURE_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
        print("--------------------------------------------------")
        print(f"SESSION SUMMARY:")
        print(f"- Peak Concurrent Students: {max_students_seen}")
        print(f"- Total Meal Plates Monitored: {total_plates_served}")
        print("--------------------------------------------------")

if __name__ == "__main__":
    run_continuous_monitor()
