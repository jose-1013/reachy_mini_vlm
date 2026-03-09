import cv2
import requests
from flask import Flask, Response, request, jsonify

app = Flask(__name__)

print("Opening cameras...")

cam1 = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cam2 = cv2.VideoCapture(1, cv2.CAP_DSHOW)

cam1.set(cv2.CAP_PROP_FRAME_WIDTH,640)
cam1.set(cv2.CAP_PROP_FRAME_HEIGHT,360)

cam2.set(cv2.CAP_PROP_FRAME_WIDTH,640)
cam2.set(cv2.CAP_PROP_FRAME_HEIGHT,360)

print("Cameras ready")

VLM1 = "http://127.0.0.1:5000/caption"
VLM2 = "http://127.0.0.1:5001/caption"


# -----------------------------
# camera stream
# -----------------------------

def gen_frames(camera):

    while True:

        success, frame = camera.read()

        if not success:
            continue

        _, buffer = cv2.imencode('.jpg', frame)

        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/camera1')
def camera1():
    return Response(
        gen_frames(cam1),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/camera2')
def camera2():
    return Response(
        gen_frames(cam2),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


# -----------------------------
# detect
# -----------------------------

def vlm_caption(frame, url):

    _, img = cv2.imencode(".jpg", frame)

    files = {
        "image":("frame.jpg",img.tobytes(),"image/jpeg")
    }

    r = requests.post(url,files=files,timeout=20)

    caption = r.json()["caption"]

    if "ASSISTANT:" in caption:
        caption = caption.split("ASSISTANT:")[-1]

    return caption.lower()


@app.route("/detect",methods=["POST"])
def detect():

    robot = request.form["robot"]
    target = request.form["target"].lower()

    if robot == "1":
        cam = cam1
        vlm = VLM1
    else:
        cam = cam2
        vlm = VLM2

    ret,frame = cam.read()

    if not ret:
        return jsonify({
            "found":False,
            "caption":"camera error"
        })

    caption = vlm_caption(frame,vlm)

    found = target in caption

    return jsonify({
        "found":found,
        "caption":caption
    })


# -----------------------------
# web page
# -----------------------------

@app.route("/")
def home():

    return """
    <h1>Dual Reachy Camera View</h1>

    <h2>Robot 1</h2>
    <img src="/camera1" width="640">

    <h2>Robot 2</h2>
    <img src="/camera2" width="640">
    """


# -----------------------------
# run
# -----------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=7000,
        threaded=True
    )