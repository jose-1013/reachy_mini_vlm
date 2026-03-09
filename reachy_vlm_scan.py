import cv2
import requests
import random
import time

VLM_URL = "http://127.0.0.1:5000/caption"
MOVE_URL = "http://127.0.0.1:8000/api/move/goto"
WAKE_URL = "http://127.0.0.1:8000/api/move/play/wake_up"
SLEEP_URL = "http://127.0.0.1:8000/api/move/play/goto_sleep"

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

scan_mode = False

print("Waking Reachy...")
requests.post(WAKE_URL)
time.sleep(3)

# 머리 고정 (위로)
requests.post(
    MOVE_URL,
    json={
        "head_pitch": -1.0,
        "head_yaw": 0,
        "duration": 1.5
    }
)

print("Reachy ready")
print("Press M to scan once")
print("Press Q to quit")

while True:

    ret, frame = cap.read()

    if not ret or frame is None:
        print("Frame error")
        continue

    cv2.imshow("camera", frame)

    key = cv2.waitKey(1) & 0xFF

    # 종료
    if key == ord('q'):
        print("Sleeping Reachy")
        requests.post(SLEEP_URL)
        break

    # 스캔 시작
    if key == ord('m'):
        print("\nScan triggered")
        scan_mode = True

    if scan_mode:

        # 몸통 좌우 회전
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

        time.sleep(1)

        # 이미지 인코딩
        _, img_encoded = cv2.imencode(".jpg", frame)

        files = {
            "image": ("frame.jpg", img_encoded.tobytes(), "image/jpeg")
        }

        try:

            r = requests.post(VLM_URL, files=files, timeout=10)

            if r.status_code != 200:
                print("VLM request failed:", r.status_code)
                scan_mode = False
                continue

            result = r.json()
            caption = result.get("caption", "")

            # 프롬프트 제거
            if "ASSISTANT:" in caption:
                caption = caption.split("ASSISTANT:")[-1].strip()

            print("\nCaption:", caption)

            # 사람 탐지
            if "person" in caption.lower():

                print("\nPERSON DETECTED")

                antenna_l = random.uniform(-0.8, 0.8)
                antenna_r = random.uniform(-0.8, 0.8)

                requests.post(
                    MOVE_URL,
                    json={
                        "antennas": [antenna_l, antenna_r],
                        "duration": 1
                    }
                )

                words = caption.split()

                line1 = " ".join(words[:6])
                line2 = " ".join(words[6:12])

                print(line1)
                print(line2)

        except Exception as e:
            print("VLM error:", e)

        scan_mode = False

cap.release()
cv2.destroyAllWindows()

print("Program terminated")