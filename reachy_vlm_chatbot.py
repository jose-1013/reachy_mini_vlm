from openai import OpenAI
from dotenv import load_dotenv
import os
import cv2
import requests
import random
import time

# 환경 변수
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 서버 주소
VLM_URL = "http://127.0.0.1:5000/caption"

MOVE_URL = "http://127.0.0.1:8000/api/move/goto"
WAKE_URL = "http://127.0.0.1:8000/api/move/play/wake_up"
SLEEP_URL = "http://127.0.0.1:8000/api/move/play/goto_sleep"

# Reachy 깨우기
print("Waking Reachy...")
try:
    requests.post(WAKE_URL)
except:
    print("Reachy wake failed")

# 카메라
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera open failed")
    exit()

# 카메라 해상도
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

# 창 설정
cv2.namedWindow("camera", cv2.WINDOW_NORMAL)
cv2.resizeWindow("camera", 640, 360)
cv2.moveWindow("camera", 200, 100)

print("Reachy Vision Chat Agent")
print("Commands:")
print("  what do you see  → vision")
print("  look around      → scan environment")
print("  q                → quit")

conversation = [
    {
        "role": "system",
        "content": "You are a friendly robot named Reachy."
    }
]


# -----------------------------
# Vision
# -----------------------------

def ask_vision():

    for _ in range(3):
        ret, frame = cap.read()

    if not ret:
        return "Camera error."

    cv2.imshow("camera", frame)
    cv2.waitKey(1)

    _, img_encoded = cv2.imencode(".jpg", frame)

    files = {
        "image": ("frame.jpg", img_encoded.tobytes(), "image/jpeg")
    }

    try:

        r = requests.post(VLM_URL, files=files, timeout=20)

        if r.status_code != 200:
            return "Vision server error."

        result = r.json()
        caption = result.get("caption", "")

        if "ASSISTANT:" in caption:
            caption = caption.split("ASSISTANT:")[-1].strip()

        return caption

    except:
        return "Vision request failed."


# -----------------------------
# Look Around (scan)
# -----------------------------

def look_around():

    results = []

    print("\nScanning environment...\n")

    for i in range(3):

        body_yaw = random.uniform(-1.2, 1.2)

        requests.post(
            MOVE_URL,
            json={
                "body_yaw": body_yaw,
                "head_pitch": -1.0,
                "head_yaw": 0,
                "duration": 1.5
            }
        )

        time.sleep(2)

        ret, frame = cap.read()

        if not ret:
            continue

        cv2.imshow("camera", frame)
        cv2.waitKey(1)

        _, img_encoded = cv2.imencode(".jpg", frame)

        files = {
            "image": ("frame.jpg", img_encoded.tobytes(), "image/jpeg")
        }

        try:

            r = requests.post(VLM_URL, files=files, timeout=10)

            if r.status_code != 200:
                continue

            result = r.json()
            caption = result.get("caption", "")

            if "ASSISTANT:" in caption:
                caption = caption.split("ASSISTANT:")[-1].strip()

            print("view", i+1, ":", caption)

            results.append(caption)

        except:
            continue

    if len(results) == 0:
        return "I could not see anything."

    return " | ".join(results)


# -----------------------------
# Main loop
# -----------------------------

while True:

    user = input("User: ")

    # 종료
    if user.lower() in ["q", "quit"]:
        print("Sleeping Reachy...")
        try:
            requests.post(SLEEP_URL)
        except:
            print("Sleep command failed")
        break

    # look around
    if "look around" in user.lower() or "scan" in user.lower():

        result = look_around()

        print("\nReachy:", result)

        conversation.append({"role": "user", "content": user})
        conversation.append({"role": "assistant", "content": result})

        continue

    # vision
    if "see" in user.lower() or "look" in user.lower():

        vision_result = ask_vision()

        print("Reachy:", vision_result)

        conversation.append({"role": "user", "content": user})
        conversation.append({"role": "assistant", "content": vision_result})

        continue

    # 일반 대화
    conversation.append({"role": "user", "content": user})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation
    )

    reply = response.choices[0].message.content

    print("Reachy:", reply)

    conversation.append({"role": "assistant", "content": reply})


cap.release()
cv2.destroyAllWindows()

print("Program terminated")