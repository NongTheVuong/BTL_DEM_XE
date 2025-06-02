from flask import Flask, request
import os
import datetime

app = Flask(__name__)
SAVE_DIR = "frames"
os.makedirs(SAVE_DIR, exist_ok=True)

@app.route("/upload_frame", methods=["POST"])
def upload_frame():
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(SAVE_DIR, f"frame_{now}.jpg")
    try:
        with open(filename, "wb") as f:
            f.write(request.data)
        print(f"✅ Đã lưu ảnh: {filename}")
        return "OK", 200
    except Exception as e:
        print(f"❌ Lỗi khi lưu ảnh: {e}")
        return "Lỗi server", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
