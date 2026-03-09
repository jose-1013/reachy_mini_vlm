from flask import Flask, request, jsonify
from PIL import Image
from transformers import AutoModelForCausalLM, AutoTokenizer

app = Flask(__name__)

print("Loading VLM...")

model = AutoModelForCausalLM.from_pretrained(
    "vikhyatk/moondream2",
    trust_remote_code=True
)

tokenizer = AutoTokenizer.from_pretrained(
    "vikhyatk/moondream2",
    trust_remote_code=True
)

print("VLM ready")


@app.route("/caption", methods=["POST"])
def caption():

    image = Image.open(request.files["image"])

    result = model.caption(image)

    return jsonify({"caption": result["caption"]})


app.run(host="127.0.0.1", port=5000)