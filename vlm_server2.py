import torch
from transformers import AutoProcessor, LlavaForConditionalGeneration
from flask import Flask, request, jsonify
from PIL import Image
import io

app = Flask(__name__)

print("Loading VLM2 model...")

model_id = "llava-hf/llava-1.5-7b-hf"

processor = AutoProcessor.from_pretrained(model_id)

model = LlavaForConditionalGeneration.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    device_map="auto"
)

device = "cuda" if torch.cuda.is_available() else "cpu"

print("VLM2 loaded")

@app.route("/caption", methods=["POST"])
def caption():

    try:

        if "image" not in request.files:
            return jsonify({"error": "no image"}), 400

        file = request.files["image"]
        image = Image.open(io.BytesIO(file.read())).convert("RGB")

        prompt = "USER: <image>\nDescribe the image in one sentence.\nASSISTANT:"

        inputs = processor(
            text=prompt,
            images=image,
            return_tensors="pt"
        )

        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():

            output = model.generate(
                **inputs,
                max_new_tokens=50,
                do_sample=False
            )

        result = processor.batch_decode(output, skip_special_tokens=True)[0]

        return jsonify({"caption": result})

    except Exception as e:

        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return "VLM2 server running"


if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5001)