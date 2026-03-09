import requests
import threading
import time
import random

R1_MOVE = "http://127.0.0.1:8000/api/move/goto"
R2_MOVE = "http://127.0.0.1:8001/api/move/goto"

R1_WAKE = "http://127.0.0.1:8000/api/move/play/wake_up"
R2_WAKE = "http://127.0.0.1:8001/api/move/play/wake_up"

R1_SLEEP = "http://127.0.0.1:8000/api/move/play/goto_sleep"
R2_SLEEP = "http://127.0.0.1:8001/api/move/play/goto_sleep"

DETECT = "http://127.0.0.1:7000/detect"

found_event = threading.Event()
stop_event = threading.Event()


# -----------------------------
# move robot
# -----------------------------

def move_robot(url, body, head):

    requests.post(
        url,
        json={
            "body_yaw": body,
            "head_pitch": -1,
            "head_yaw": head,
            "duration": 1
        }
    )

    time.sleep(1.2)


# -----------------------------
# robot search
# -----------------------------

def robot_search(name, robot_id, move_url, body_positions, heads, target):

    print(name, "search start")

    for body in body_positions:

        if found_event.is_set() or stop_event.is_set():
            return

        for head in heads:

            if found_event.is_set() or stop_event.is_set():
                return

            print(name, "move", body, head)

            move_robot(move_url, body, head)

            r = requests.post(
                DETECT,
                data={
                    "robot": robot_id,
                    "target": target
                }
            )

            result = r.json()

            print(name, "sees:", result["caption"])

            if result["found"]:

                print("\nFOUND BY", name)

                found_event.set()
                return


# -----------------------------
# dual search
# -----------------------------

def dual_search(target):

    left = [-2, -1, -0.4]
    right = [0.4, 1, 2]

    heads = [-0.8, 0, 0.8]

    random.shuffle(left)
    random.shuffle(right)

    t1 = threading.Thread(
        target=robot_search,
        args=("Robot1","1",R1_MOVE,left,heads,target)
    )

    t2 = threading.Thread(
        target=robot_search,
        args=("Robot2","2",R2_MOVE,right,heads,target)
    )

    t1.start()
    t2.start()

    while t1.is_alive() or t2.is_alive():

        if found_event.is_set() or stop_event.is_set():
            break

        time.sleep(0.1)


# -----------------------------
# keyboard stop
# -----------------------------

def keyboard_listener():

    while True:

        key = input()

        if key.lower() == "s":

            print("\nSTOP requested")

            stop_event.set()
            return


# -----------------------------
# wake / sleep
# -----------------------------

def wake():

    print("Waking robots")

    requests.post(R1_WAKE)
    requests.post(R2_WAKE)

    time.sleep(4)


def sleep():

    print("Sleeping robots")

    requests.post(R1_SLEEP)
    requests.post(R2_SLEEP)

    time.sleep(3)


# -----------------------------
# main
# -----------------------------

wake()

while True:

    target = input("\nTarget object (q to quit): ")

    if target == "q":
        break

    found_event.clear()
    stop_event.clear()

    print("\nPress 's' to stop search\n")

    listener = threading.Thread(target=keyboard_listener)
    listener.daemon = True
    listener.start()

    while not found_event.is_set() and not stop_event.is_set():

        dual_search(target)

    if found_event.is_set():
        print("\nTarget found. Waiting next command.")

    if stop_event.is_set():
        print("\nSearch stopped manually.")


sleep()

print("Program terminated")