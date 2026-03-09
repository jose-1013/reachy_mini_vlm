import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""

from flask import Flask, request, jsonify
from PIL import Image
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

app = Flask(__name__)

print("Loading Qwen2-VL...")

model_id = "Qwen/Qwen2-VL-7B-Instruct"

processor = AutoProcessor.from_pretrained(model_id)

model = Qwen2VLForConditionalGeneration.from_pretrained(
    model_id,
    torch_dtype=torch.float32,
    device_map={"": "cpu"}
)

device = "cpu"
model.to(device)

print("Model loaded (CPU mode)")


@app.route("/caption", methods=["POST"])
def caption():

    try:

        image = Image.open(request.files["image"]).convert("RGB")

        prompt = "Describe the person and the scene briefly."

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        text = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = processor(
            text=[text],
            images=[image],
            return_tensors="pt"
        )

        output = model.generate(
            **inputs,
            max_new_tokens=60
        )

        caption = processor.batch_decode(
            output,
            skip_special_tokens=True
        )[0]

        return jsonify({"caption": caption})

    except Exception as e:

        print("VLM ERROR:", e)
        return jsonify({"caption": ""})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)