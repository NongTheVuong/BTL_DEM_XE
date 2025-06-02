import cv2
import numpy as np
import csv
import pandas as pd
import matplotlib.pyplot as plt
from ultralytics import YOLO
from sort import Sort

import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# === BƯỚC 1: VẼ 4 ĐƯỜNG THỦ CÔNG ===
lines = []
clicks = []
waiting_for_q = False
directions = ["East", "West", "South", "North"]

def mouse_callback(event, x, y, flags, param):
    global clicks, lines, waiting_for_q
    if event == cv2.EVENT_LBUTTONDOWN and not waiting_for_q:
        clicks.append((x, y))
        if len(clicks) == 1:
            print("📍 Đã chọn điểm 1.")
        elif len(clicks) == 2:
            print("📍 Đã chọn điểm 2. ➡️ Ấn 'q' để xác nhận đường.")
            lines.append((clicks[0], clicks[1]))
            clicks = []
            waiting_for_q = True

video_path = "frames/xe2.mp4"
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print(f"❌ Không thể mở video: {video_path}")
    exit()

# Lấy kích thước thật của video
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"📐 Kích thước video: {width} x {height}")

ret, frame = cap.read()
if not ret:
    print("❌ Không thể đọc frame đầu.")
    cap.release()
    exit()

cv2.namedWindow("Ve_duong", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Ve_duong", width, height)
cv2.setMouseCallback("Ve_duong", mouse_callback)

print("🖱 Click chuột trái để chọn điểm 1 và điểm 2.")
print("✅ Sau mỗi đường, ấn 'q' để xác nhận.")
print("❌ Ấn 'r' để hủy điểm hoặc đường đang vẽ.")

while True:
    temp = frame.copy()
    for i, line in enumerate(lines):
        cv2.line(temp, line[0], line[1], (0, 255, 255), 2)
        name = directions[i] if i < len(directions) else f"Line {i+1}"
        cv2.putText(temp, name, line[0], cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    if len(clicks) == 1:
        cv2.circle(temp, clicks[0], 5, (0, 0, 255), -1)

    cv2.imshow("Ve_duong", temp)
    key = cv2.waitKey(1)

    if waiting_for_q and key == ord('q'):
        waiting_for_q = False
        print(f"✅ Đã xác nhận đường {len(lines)}.")
    if key == ord('r'):
        if waiting_for_q and len(lines) > 0:
            removed = lines.pop()
            print(f"❌ Đã hủy đường {len(lines)+1}: {removed}")
            waiting_for_q = False
        elif len(clicks) == 1:
            print("❌ Đã hủy điểm 1.")
            clicks = []
    if len(lines) == 4:
        break

cv2.destroyAllWindows()
cap.release()
print("➡️ Đã vẽ đủ 4 đường. Bắt đầu chạy video...")

# === BƯỚC 2: TRACKING, ĐẾM HƯỚNG VÀ GHI CSV ===
cap = cv2.VideoCapture(video_path)
model = YOLO("yolov5s.pt")
tracker = Sort()

track_memory = {}
track_direction = {}
logged_ids = set()
active_ids = set()
csv_filename = "xe_di_qua.csv"

with open(csv_filename, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["ID", "Huong"])

cv2.namedWindow("Tracking_with_Direction", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Tracking_with_Direction", width, height)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, conf=0.2, iou=0.4, verbose=False)[0]
    dets = []
    current_ids = set()

    for box in results.boxes:
        cls = int(box.cls[0])
        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        if cls in [2, 3]:
            dets.append([x1, y1, x2, y2, conf])

    dets = np.array(dets)
    tracks = tracker.update(dets)

    for track in tracks:
        x1, y1, x2, y2, track_id = map(int, track)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        current_ids.add(track_id)

        if track_id in track_memory:
            prev_x, prev_y = track_memory[track_id]
            dx, dy = cx - prev_x, cy - prev_y
            direction = "East" if abs(dx) > abs(dy) and dx > 0 else \
                        "West" if abs(dx) > abs(dy) else \
                        "South" if dy > 0 else "North"
            track_direction[track_id] = direction
        else:
            track_direction[track_id] = "..."
        track_memory[track_id] = (cx, cy)

        label = f"ID:{track_id} {track_direction[track_id]}"
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
        cv2.putText(frame, label, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    disappeared_ids = active_ids - current_ids
    for lost_id in disappeared_ids:
        if lost_id not in logged_ids and track_direction.get(lost_id, "...") != "...":
            logged_ids.add(lost_id)
            with open(csv_filename, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([lost_id, track_direction[lost_id]])
    active_ids = current_ids

    for i, line in enumerate(lines):
        pt1, pt2 = line
        cv2.line(frame, pt1, pt2, (0, 255, 255), 2)
        mid_x = (pt1[0] + pt2[0]) // 2
        mid_y = (pt1[1] + pt2[1]) // 2
        name = directions[i] if i < len(directions) else f"Line {i+1}"
        cv2.putText(frame, name, (mid_x, mid_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Tracking_with_Direction", frame)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print(f"✅ Đã lưu dữ liệu vào {csv_filename}")

# === BIỂU ĐỒ THỐNG KÊ ===
try:
    df = pd.read_csv(csv_filename)
    print("\n📊 Thống kê số lượng xe theo hướng:")
    counts = df['Huong'].value_counts()
    print(counts)

    plt.figure(figsize=(6,4))
    counts.plot(kind='bar', color='skyblue')
    plt.title('Số lượng xe theo hướng')
    plt.xlabel('Hướng')
    plt.ylabel('Số xe')
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig("thong_ke.png")
    plt.show()
except Exception as e:
    print(f"❌ Lỗi khi đọc CSV: {e}")

# === GOOGLE DRIVE UPLOAD ===
def upload_to_drive(file_path, file_name):
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('drive', 'v3', credentials=creds)
    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_path, mimetype='text/csv')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"📤 Đã upload lên Google Drive. File ID: {file.get('id')}")

upload_to_drive(csv_filename, csv_filename)
