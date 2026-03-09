import requests
import cv2
import time
import traceback

# ======================
# CONFIG
# ======================

R1 = "http://127.0.0.1:8000"
R2 = "http://127.0.0.1:8001"

VLM = "http://127.0.0.1:5000/caption"

# ======================
# STEP 1 : API CHECK
# ======================

def check_reachy_api():

    print("\n===== REACHY API TEST =====")

    try:

        r1 = requests.get(R1, timeout=3)
        print("Robot1 API:", r1.status_code)

    except:
        print("Robot1 API FAILED")

    try:

        r2 = requests.get(R2, timeout=3)
        print("Robot2 API:", r2.status_code)

    except:
        print("Robot2 API FAILED")


# ======================
# STEP 2 : ROBOT MOVE TEST
# ======================

def test_robot_move():

    print("\n===== ROBOT MOVE TEST =====")

    try:

        print("Robot1 move")

        requests.post(
            f"{R1}/api/move/goto",
            json={
                "body_yaw": 1,
                "head_pitch": -1,
                "head_yaw": 0,
                "duration": 2
            }
        )

        time.sleep(3)

        print("Robot2 move")

        requests.post(
            f"{R2}/api/move/goto",
            json={
                "body_yaw": -1,
                "head_pitch": -1,
                "head_yaw": 0,
                "duration": 2
            }
        )

        print("Movement OK")

    except:

        print("Movement FAILED")
        traceback.print_exc()


# ======================
# STEP 3 : CAMERA TEST
# ======================

def test_camera():

    print("\n===== CAMERA TEST =====")

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():

        print("Camera open FAILED")
        return None

    print("Camera OK")

    ret, frame = cap.read()

    if not ret:

        print("Frame read FAILED")
        return None

    cv2.imshow("debug_camera", frame)
    cv2.waitKey(1000)

    cap.release()
    cv2.destroyAllWindows()

    print("Camera frame captured")

    return frame


# ======================
# STEP 4 : VLM TEST
# ======================

def test_vlm(frame):

    print("\n===== VLM TEST =====")

    try:

        _, img = cv2.imencode(".jpg", frame)

        files = {
            "image": ("frame.jpg", img.tobytes(), "image/jpeg")
        }

        r = requests.post(VLM, files=files, timeout=10)

        if r.status_code != 200:

            print("VLM request FAILED")
            return

        caption = r.json().get("caption","")

        print("VLM CAPTION:")
        print(caption)

    except:

        print("VLM FAILED")
        traceback.print_exc()


# ======================
# MAIN
# ======================

print("\n==========================")
print("DUAL REACHY DEBUG TOOL")
print("==========================")

check_reachy_api()

test_robot_move()

frame = test_camera()

if frame is not None:

    test_vlm(frame)

print("\nDEBUG COMPLETE")