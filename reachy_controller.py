from fastapi import FastAPI
import requests

app = FastAPI()

REACHY_URL = "http://127.0.0.1:8000/api/move/goto"

@app.post("/track")

def track(data: dict):

    yaw = data["yaw"]

    requests.post(
        REACHY_URL,
        json={
            "head_pose":{
                "yaw": yaw
            },
            "duration":0.8
        }
    )

    return {"status":"ok"}