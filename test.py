import requests

url = "http://127.0.0.1:5000/caption"

image_path = "test.jpg"

with open(image_path, "rb") as f:
    files = {"image": f}
    response = requests.post(url, files=files)

print("status:", response.status_code)
print("response:", response.text)