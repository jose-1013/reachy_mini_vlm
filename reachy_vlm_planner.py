from openai import OpenAI
from dotenv import load_dotenv
import os
import cv2
import requests
import random
import time

# API
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# servers
VLM_URL = "http://127.0.0.1:5000/caption"
MOVE_URL = "http://127.0.0.1:8000/api/move/goto"
WAKE_URL = "http://127.0.0.1:8000/api/move/play/wake_up"
SLEEP_URL = "http://127.0.0.1:8000/api/move/play/goto_sleep"

# wake robot
print("Waking Reachy...")
requests.post(WAKE_URL)
time.sleep(2)

# camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera open failed")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

cv2.namedWindow("camera", cv2.WINDOW_NORMAL)
cv2.resizeWindow("camera", 640, 360)
cv2.moveWindow("camera", 200, 100)


# --------------------------
# VLM
# --------------------------

def caption_image(frame):

    _, img_encoded = cv2.imencode(".jpg", frame)

    files = {
        "image": ("frame.jpg", img_encoded.tobytes(), "image/jpeg")
    }

    r = requests.post(VLM_URL, files=files, timeout=15)

    if r.status_code != 200:
        return None

    result = r.json()
    caption = result.get("caption", "")

    if "ASSISTANT:" in caption:
        caption = caption.split("ASSISTANT:")[-1].strip()

    return caption


# --------------------------
# Scan environment
# --------------------------

def scan_environment():

    scenes = []

    print("\nScanning environment...\n")

    for i in range(4):

        yaw = random.uniform(-1.2, 1.2)

        requests.post(
            MOVE_URL,
            json={
                "body_yaw": yaw,
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

        caption = caption_image(frame)

        if caption:
            print(f"view {i+1}: {caption}")
            scenes.append(caption)

    return scenes


# --------------------------
# Planner
# --------------------------

def plan_task(goal, scenes):

    scene_text = "\n".join(scenes)

    prompt = f"""
You are a robot planning system.

User goal:
{goal}

Observed environment descriptions:
{scene_text}

Important rules:
- Only use objects that appear in the scene descriptions.
- Do NOT assume objects that are not mentioned.
- If the environment is unclear, include a step to observe again.
- Do NOT hallucinate new objects.

Create a short step-by-step plan.

Plan:
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return response.choices[0].message.content


# --------------------------
# Main
# --------------------------

print("\nReachy VLM Planner")
print("type 'q' to quit\n")

while True:

    query = input("Query: ")

    if query.lower() in ["q","quit"]:
        break

    scenes = scan_environment()

    if len(scenes) == 0:
        print("No scene information.")
        continue

    plan = plan_task(query, scenes)

    print("\n--- PLAN ---\n")
    print(plan)
    print("\n------------\n")


# shutdown
print("Sleeping Reachy...")
requests.post(SLEEP_URL)

cap.release()
cv2.destroyAllWindows()