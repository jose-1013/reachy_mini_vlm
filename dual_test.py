import requests
import time
import sys
import traceback

# -----------------------------
# Robot URLs
# -----------------------------

R1_MOVE = "http://127.0.0.1:8000/api/move/goto"
R2_MOVE = "http://127.0.0.1:8001/api/move/goto"

R1_WAKE = "http://127.0.0.1:8000/api/move/play/wake_up"
R2_WAKE = "http://127.0.0.1:8001/api/move/play/wake_up"

R1_SLEEP = "http://127.0.0.1:8000/api/move/play/goto_sleep"
R2_SLEEP = "http://127.0.0.1:8001/api/move/play/goto_sleep"


# -----------------------------
# Move helper
# -----------------------------

def move_robot(url, body, head):

    requests.post(
        url,
        json={
            "body_yaw": body,
            "head_pitch": -1.0,
            "head_yaw": head,
            "duration": 1.2
        },
        timeout=5
    )


# -----------------------------
# Main
# -----------------------------

def main():

    print("Waking robots...")

    requests.post(R1_WAKE)
    requests.post(R2_WAKE)

    time.sleep(3)

    print("Starting dual movement test")

    for i in range(5):

        print("Step", i+1)

        move_robot(R1_MOVE, 1.5, 0.5)
        move_robot(R2_MOVE, -1.5, -0.5)

        time.sleep(2)

        move_robot(R1_MOVE, -1.5, -0.5)
        move_robot(R2_MOVE, 1.5, 0.5)

        time.sleep(2)

    print("Sleeping robots")

    requests.post(R1_SLEEP)
    requests.post(R2_SLEEP)


# -----------------------------
# Safe run
# -----------------------------

if __name__ == "__main__":

    try:
        main()

    except Exception:

        print("\n❌ ERROR OCCURRED\n")
        traceback.print_exc()

        try:
            requests.post(R1_SLEEP)
            requests.post(R2_SLEEP)
        except:
            pass

        sys.exit(1)