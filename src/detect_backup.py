import cv2
import numpy as np
import onnxruntime as ort

from database import save_record
from meal_verification import verify_meal
from meal_schedule import get_today_meal


MODEL_PATH = "models/yolov8n.onnx"
IMAGE_PATH = "images/meal_test.jpg"
OUTPUT_PATH = "outputs/detected.jpg"


# COCO class names
CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane",
    "bus", "train", "truck", "boat", "traffic light",
    "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat",
    "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon",
    "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
    "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet",
    "tv", "laptop", "mouse", "remote", "keyboard", "cell phone",
    "microwave", "oven", "toaster", "sink", "refrigerator",
    "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush"
]


CONFIDENCE = 0.40
NMS_THRESHOLD = 0.45
IMAGE_SIZE = 640


# --------------------------------------------------
# LOAD YOLO MODEL
# --------------------------------------------------

session = ort.InferenceSession(MODEL_PATH)

input_name = session.get_inputs()[0].name


# --------------------------------------------------
# READ IMAGE
# --------------------------------------------------

image = cv2.imread(IMAGE_PATH)

if image is None:
    raise FileNotFoundError(
        "Test image not found!"
    )


original_h, original_w = image.shape[:2]


# --------------------------------------------------
# PREPROCESS IMAGE
# --------------------------------------------------

img = cv2.resize(
    image,
    (IMAGE_SIZE, IMAGE_SIZE)
)

img = cv2.cvtColor(
    img,
    cv2.COLOR_BGR2RGB
)

img = img.astype(
    np.float32
) / 255.0

img = np.transpose(
    img,
    (2, 0, 1)
)

img = np.expand_dims(
    img,
    axis=0
)


# --------------------------------------------------
# YOLO INFERENCE
# --------------------------------------------------

output = session.run(
    None,
    {
        input_name: img
    }
)[0]

output = output[0].transpose()


boxes = []
scores = []
class_ids = []


x_scale = original_w / IMAGE_SIZE
y_scale = original_h / IMAGE_SIZE


# --------------------------------------------------
# PROCESS DETECTIONS
# --------------------------------------------------

for detection in output:

    x, y, w, h = detection[:4]

    class_scores = detection[4:]

    class_id = np.argmax(
        class_scores
    )

    confidence = class_scores[class_id]

    if confidence < CONFIDENCE:
        continue


    left = int(
        (x - w / 2) * x_scale
    )

    top = int(
        (y - h / 2) * y_scale
    )

    width = int(
        w * x_scale
    )

    height = int(
        h * y_scale
    )


    boxes.append([
        left,
        top,
        width,
        height
    ])

    scores.append(
        float(confidence)
    )

    class_ids.append(
        int(class_id)
    )


# --------------------------------------------------
# NON-MAXIMUM SUPPRESSION
# --------------------------------------------------

indices = cv2.dnn.NMSBoxes(
    boxes,
    scores,
    CONFIDENCE,
    NMS_THRESHOLD
)


# --------------------------------------------------
# COUNT PERSONS
# --------------------------------------------------

person_count = 0


if len(indices) > 0:

    for i in indices.flatten():

        x, y, w, h = boxes[i]

        class_id = class_ids[i]

        confidence = scores[i]


        label = (
            f"{CLASSES[class_id]} "
            f"{confidence:.2f}"
        )


        # Bounding box
        cv2.rectangle(
            image,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )


        # Label
        cv2.putText(
            image,
            label,
            (x, max(y - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )


        # Person count
        if CLASSES[class_id] == "person":

            person_count += 1


# --------------------------------------------------
# PLATE DETECTION
# --------------------------------------------------

# Actual plate detection model
# will be integrated later.

plate_count = None


# --------------------------------------------------
# MEAL VERIFICATION
# --------------------------------------------------

meal_status = verify_meal(
    person_count,
    plate_count
)


# --------------------------------------------------
# GET TODAY'S MEAL
# --------------------------------------------------

today, scheduled_meal = get_today_meal()


# --------------------------------------------------
# SAVE OUTPUT IMAGE
# --------------------------------------------------

cv2.imwrite(
    OUTPUT_PATH,
    image
)


# --------------------------------------------------
# SAVE RECORD TO DATABASE
# --------------------------------------------------

save_record(
    person_count=person_count,
    plate_count=plate_count,
    scheduled_meal=scheduled_meal,
    meal_status=meal_status
)


# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------

print()
print("================================")
print("     SIH MEAL MONITORING")
print("================================")

print("Detection complete!")

print("Today:", today)

print(
    "Scheduled Meal:",
    scheduled_meal
)

print(
    "Persons detected:",
    person_count
)

print(
    "Plate count:",
    plate_count
)

print(
    "Meal status:",
    meal_status
)

print("Database record saved!")

print(
    "Output saved:",
    OUTPUT_PATH
)

print("================================")