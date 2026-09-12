import sys
import cv2
import numpy as np
import onnxruntime as ort

from database import save_record
from meal_schedule import get_today_meal
from meal_verification import verify_meal
from plate_detector import detect_plates

# -----------------------------
# MODEL / FILE SETTINGS
# -----------------------------

PERSON_MODEL = "models/yolov8n.onnx"
DEFAULT_IMAGE = "images/midday.png"
OUTPUT_PATH = "outputs/detected.jpg"

INPUT_SIZE = 640
CONF_THRESHOLD = 0.40
NMS_THRESHOLD = 0.45


def draw_label(image, text, x, y, color):
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.55
    thickness = 1
    (text_w, text_h), _ = cv2.getTextSize(text, font, scale, thickness)

    box_y1 = max(0, y - text_h - 8)
    box_y2 = y
    box_x1 = x
    box_x2 = x + text_w + 8

    cv2.rectangle(image, (box_x1, box_y1), (box_x2, box_y2), color, -1)
    cv2.putText(
        image,
        text,
        (box_x1 + 4, box_y2 - 4),
        font,
        scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )


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
        cx, cy, bw, bh = pred[:4]
        confidence = float(pred[4])

        if confidence < CONF_THRESHOLD:
            continue

        x1 = int((cx - bw / 2) * original_w / INPUT_SIZE)
        y1 = int((cy - bh / 2) * original_h / INPUT_SIZE)
        box_w = int(bw * original_w / INPUT_SIZE)
        box_h = int(bh * original_h / INPUT_SIZE)

        boxes.append([x1, y1, box_w, box_h])
        scores.append(confidence)

    if not boxes:
        return []

    indices = cv2.dnn.NMSBoxes(
        boxes,
        scores,
        CONF_THRESHOLD,
        NMS_THRESHOLD,
    )

    results = []
    for i in indices:
        i = int(i)
        results.append({
            "box": boxes[i],
            "confidence": scores[i],
        })

    return results


def main():
    image_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IMAGE

    print("--------------------------------")
    print("SIH MEAL MONITORING PIPELINE")
    print(f"Target Image: {image_path}")
    print("--------------------------------")

    day_name, today_meal = get_today_meal()
    print(f"Day: {day_name} | Scheduled Meal: {today_meal}")

    print("Loading person model...")
    person_session = ort.InferenceSession(PERSON_MODEL)
    person_input = person_session.get_inputs()[0].name

    image = cv2.imread(image_path)
    if image is None:
        print("ERROR: Image not found:", image_path)
        return

    # 1. Person Detection
    person_results = detect_persons(image, person_session, person_input)
    person_count = len(person_results)
    print("Students detected:", person_count)

    for detection in person_results:
        x, y, w, h = detection["box"]
        cv2.rectangle(image, (x, y), (x + w, y + h), (255, 100, 0), 2)
        draw_label(image, f"Student {detection['confidence']:.2f}", x, y, (255, 100, 0))

    # 2. Plate Detection
    print("Detecting plates...")
    plate_count, plate_results = detect_plates(image)
    print("Plates detected:", plate_count)

    for detection in plate_results:
        x, y, w, h = detection["box"]
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 180, 0), 2)
        draw_label(image, f"Plate {detection['confidence']:.2f}", x, y, (0, 180, 0))

    # 3. Meal Verification
    meal_status = verify_meal(person_count, plate_count)
    print("Meal status:", meal_status)

    # 4. Save to Database
    save_record(
        person_count=person_count,
        plate_count=plate_count,
        scheduled_meal=today_meal,
        meal_status=meal_status,
    )

    # 5. Header Summary Overlay
    summary_text = f"Students: {person_count} | Plates: {plate_count} | Status: {meal_status}"
    cv2.rectangle(image, (0, 0), (image.shape[1], 40), (20, 24, 33), -1)
    cv2.putText(
        image,
        summary_text,
        (15, 26),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    # 6. Save Output Image
    cv2.imwrite(OUTPUT_PATH, image)
    print("Output saved:", OUTPUT_PATH)
    print("--------------------------------")


if __name__ == "__main__":
    main()
