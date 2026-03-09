import cv2
import requests
import time
import random

VLM_URL = "http://127.0.0.1:5000/caption"
REACHY_URL = "http://127.0.0.1:8000/api/move/goto"

cap = cv2.VideoCapture(0)

print("Reachy body control started")

while True:

    ret, frame = cap.read()
    if not ret:
        continue

    _, img_encoded = cv2.imencode(".jpg", frame)

    files = {
        "image": ("frame.jpg", img_encoded.tobytes(), "image/jpeg")
    }

    try:
        r = requests.post(VLM_URL, files=files)
        result = r.json()
    except Exception as e:
        print("VLM error:", e)
        continue

    caption = result.get("caption","")
    print("caption:", caption)

    if "person" in caption.lower():

        print("PERSON DETECTED")

        body_yaw = random.uniform(-1.2,1.2)

        antenna_l = random.uniform(-0.8,0.8)
        antenna_r = random.uniform(-0.8,0.8)

        requests.post(
            REACHY_URL,
            json={
                "body_yaw": body_yaw,
                "antennas":[antenna_l,antenna_r],
                "duration":1.5
            }
        )

    import cv2

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Exit requested")
        break 

    time.sleep(1)