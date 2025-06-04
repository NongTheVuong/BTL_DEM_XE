# 🚗 Hệ Thống Đếm Xe và Phát Hiện Phương Tiện Giao Thông

## 📌 Mô tả đề tài

Đây là hệ thống gồm hai chức năng chính:

1. **ESP32-CAM chụp ảnh và gửi lên Flask** để lưu ảnh giám sát thời gian thực.
2. **Phân tích video clip tại ngã tư** để đếm số lượng phương tiện và xác định hướng đi (Đông, Tây, Nam, Bắc).

---

**Cấu trúc thư mục**  
project/  
├── dem_xe/ # Mã Arduino .ino chạy trên ESP32-CAM  <br>
├── yolo_server.py # Flask server nhận ảnh từ ESP32-CAM  <br>
├── vehicle_tracker.py # Phân tích clip đếm và hướng đi  <br>
├── sort.py # Thuật toán theo dõi đối tượng SORT  <br>
├── thong_ke.png # Hình ảnh thống kê kết quả  <br>
└── .gitignore # Bỏ qua file không cần upload


Hướng dẫn chạy từng phần
**ESP32-CAM (dem_xe/)
Mở file .ino trong Arduino IDE

Chỉnh sửa SSID, mật khẩu WiFi và địa chỉ IP Flask server:

cpp
Sao chép
Chỉnh sửa
const char* ssid = "Tên_WiFi";
const char* password = "Mật_khẩu_WiFi";
const char* serverUrl = "http://<Địa_chỉ_IP_PC>:5000/upload_static";
Nạp lên ESP32-CAM

**Chạy Flask Server nhận ảnh
**Tạo Môi Trường Ảo và Chạy Dự Án

1. Mở thư mục dự án bằng VS Code
Mở VS Code → Chọn File > Open Folder... → Chọn thư mục project

2. Tạo môi trường ảo
Mở Terminal (Ctrl + ~ hoặc Terminal > New Terminal) và gõ lệnh:

python -m venv venv
Thư mục venv/ sẽ được tạo, chứa môi trường Python riêng biệt.

3. Kích hoạt môi trường ảo (trên Windows)

venv\Scripts\activate
Sau khi kích hoạt, terminal sẽ hiển thị như sau:
(venv) PS D:\...\BTL_DEM_XE>

5. Cài đặt các thư viện cần thiết

pip install flask opencv-python ultralytics pandas numpy
pip install -r requirements.txt

5. Chạy server nhận ảnh từ ESP32-CAM

python yolo_server.py
Flask server sẽ lắng nghe tại địa chỉ: http://(địa chỉ của bạn):5000

6. Chạy hệ thống đếm xe từ video

python vehicle_tracker.py

Hiển thị video với bounding box và ID xe

Nhận diện hướng đi (Đông, Tây, Nam, Bắc)

Lưu hình ảnh thống kê (thong_ke.png)

Có thể mở rộng để lưu file Excel

