from openai import OpenAI
from dotenv import load_dotenv
import os
import cv2
import requests
import time

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
# 카메라 설정
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
# Target object 추출
# -----------------------------

def extract_target(query):

    prompt = f"""
Extract the main object the robot must find.

Query:
{query}

Only output the object name.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return response.choices[0].message.content.strip().lower()


# -----------------------------
# VLM caption
# -----------------------------

def caption_image(frame):

    _, img_encoded = cv2.imencode(".jpg", frame)

    files = {
        "image": ("frame.jpg", img_encoded.tobytes(), "image/jpeg")
    }

    r = requests.post(VLM_URL, files=files, timeout=10)

    if r.status_code != 200:
        return None

    result = r.json()
    caption = result.get("caption","")

    if "ASSISTANT:" in caption:
        caption = caption.split("ASSISTANT:")[-1].strip()

    return caption.lower()


# -----------------------------
# Target search
# -----------------------------

def search_target(target):

    scan_positions = [-2.0, -1.4, -0.8, 0, 0.8, 1.4, 2.0]

    print("\nSearching for:", target)

    found = False
    scene = None

    while not found:

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

            # 카메라 안정화
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

                scene = caption
                found = True
                break

        if not found:
            print("\nTarget not found. Scanning again...\n")

    return scene


# -----------------------------
# Planner
# -----------------------------

def plan_task(query, scene):

    prompt = f"""
You are a robot planning system.

User goal:
{query}

Observed scene:
{scene}

Produce a grounded robot plan.

Your answer must contain:

1. Scene understanding
2. Object locations
3. Primary plan
4. Alternative plan

Rules:
- only use objects in the scene
- do not invent objects
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return response.choices[0].message.content


# -----------------------------
# Main
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

    if query.lower() in ["q","quit"]:
        break

    # target 추출
    target = extract_target(query)

    print("\n==============================")
    print("TARGET OBJECT :", target)
    print("==============================\n")

    # search
    scene = search_target(target)

    # planning
    plan = plan_task(query, scene)

    print("\n----------- PLAN -----------\n")
    print(plan)
    print("\n----------------------------\n")


print("Sleeping Reachy...")
requests.post(SLEEP_URL)

cap.release()
cv2.destroyAllWindows()

print("Program terminated")