import cv2
import requests
import time
import os
from openai import OpenAI
from dotenv import load_dotenv

# -----------------------------
# 환경 설정
# -----------------------------

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VLM_URL = "http://127.0.0.1:5000/caption"
MOVE_URL = "http://127.0.0.1:8000/api/move/goto"
WAKE_URL = "http://127.0.0.1:8000/api/move/play/wake_up"
SLEEP_URL = "http://127.0.0.1:8000/api/move/play/goto_sleep"

# -----------------------------
# 카메라
# -----------------------------

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera open failed")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

cv2.namedWindow("camera", cv2.WINDOW_NORMAL)
cv2.resizeWindow("camera", 640, 360)
cv2.moveWindow("camera", 200, 100)

# -----------------------------
# Query → Target object
# -----------------------------

def extract_target(query):

    prompt = f"""
Extract the physical object needed to satisfy the request.

Examples:
I'm thirsty -> cup
I want coffee -> cup
I want water -> bottle
I want to sit -> chair
I want to write -> pen

Return only ONE object word.

User request: {query}
Object:
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    target = response.choices[0].message.content.strip().lower()

    return target

# -----------------------------
# VLM caption
# -----------------------------

def caption_image(frame):

    _, img_encoded = cv2.imencode(".jpg", frame)

    files = {
        "image": ("frame.jpg", img_encoded.tobytes(), "image/jpeg")
    }

    try:

        r = requests.post(VLM_URL, files=files, timeout=15)

        if r.status_code != 200:
            print("VLM request failed")
            return None

        result = r.json()
        caption = result.get("caption", "")

        if "ASSISTANT:" in caption:
            caption = caption.split("ASSISTANT:")[-1].strip()

        return caption.lower()

    except Exception as e:
        print("VLM error:", e)
        return None

# -----------------------------
# Search
# -----------------------------

def search_target(target):

    scan_positions = [-2.0, -1.4, -0.8, 0, 0.8, 1.4, 2.0]

    print("\nSearching for:", target)

    while True:

        for pos in scan_positions:

            print("Scanning position:", pos)

            requests.post(
                MOVE_URL,
                json={
                    "body_yaw": pos,
                    "head_pitch": -1.0,
                    "head_yaw": 0,
                    "duration": 1.2
                }
            )

            time.sleep(1.5)

            for _ in range(5):
                ret, frame = cap.read()

            if not ret:
                continue

            cv2.imshow("camera", frame)
            cv2.waitKey(1)

            caption = caption_image(frame)

            if caption is None:
                continue

            print("caption:", caption)

            if target in caption:

                print("\n========== TARGET FOUND ==========\n")

                return caption

        print("\nTarget not found. scanning again...\n")

# -----------------------------
# Planning
# -----------------------------

def generate_plan(query, scene):

    prompt = f"""
You are a robot planner.

User goal:
{query}

Observed scene:
{scene}

Generate simple plan to achieve the goal.
Mention object position if possible.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

# -----------------------------
# MAIN
# -----------------------------

print("Waking Reachy...")
requests.post(WAKE_URL)

time.sleep(3)

# 머리 고정
requests.post(
    MOVE_URL,
    json={
        "head_pitch": -1.0,
        "head_yaw": 0,
        "duration": 1.5
    }
)

print("\nReachy VLM Planner")
print("type 'q' to quit\n")

while True:

    query = input("Query: ")

    if query.lower() in ["q", "quit"]:
        break

    # target extraction
    target = extract_target(query)

    print("\n==============================")
    print("TARGET OBJECT :", target)
    print("==============================\n")

    # search
    scene = search_target(target)

    # planning
    plan = generate_plan(query, scene)

    print("\n----------- PLAN -----------\n")
    print(plan)
    print("\n----------------------------\n")


print("Sleeping Reachy...")
requests.post(SLEEP_URL)

cap.release()
cv2.destroyAllWindows()

print("Program terminated")