#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include "esp_camera.h"
#include "esp_http_server.h"
#include "camera_pins.h"

const char* ssid = "AAAA";
const char* password = "15858771";
const char* yoloServer = "http://192.168.0.102:5000/upload_frame";

WebServer server(80);
httpd_handle_t stream_httpd = NULL;

// Giao diện HTML
void handleRoot() {
  server.send(200, "text/html", R"rawliteral(
    <html>
      <head><meta charset='utf-8'><title>ESP32-CAM</title></head>
      <body>
        <h2>📷 ESP32-CAM Stream + Gửi Flask</h2>
        <img src="http://192.168.0.107:81/stream" width="100%"><br><br>
        <button onclick="fetch('/capture').then(r=>r.text()).then(alert)">📸 Chụp và gửi Flask</button>
      </body>
    </html>
  )rawliteral");
}

// Chụp và gửi ảnh về Flask
void handleCapture() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    server.send(500, "text/plain", "❌ Không thể chụp ảnh");
    return;
  }

  HTTPClient http;
  http.begin(yoloServer);
  http.addHeader("Content-Type", "image/jpeg");
  int res = http.POST(fb->buf, fb->len);
  http.end();
  esp_camera_fb_return(fb);

  server.send(200, "text/plain", res > 0 ? "✅ Ảnh đã gửi về Flask!" : "❌ Gửi ảnh lỗi!");
}

// MJPEG stream handler
static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t *fb = NULL;
  esp_err_t res = ESP_OK;
  char buf[64];
  res = httpd_resp_set_type(req, "multipart/x-mixed-replace; boundary=frame");
  if (res != ESP_OK) return res;

  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("❌ Không thể lấy khung hình");
      return ESP_FAIL;
    }

    size_t hlen = snprintf(buf, sizeof(buf),
      "--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n", fb->len);
    res = httpd_resp_send_chunk(req, buf, hlen);
    res |= httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len);
    res |= httpd_resp_send_chunk(req, "\r\n", 2);
    esp_camera_fb_return(fb);

    if (res != ESP_OK) break;
  }

  return res;
}

// Khởi động MJPEG server
void startCameraStream() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 81;

  httpd_uri_t stream_uri = {
    .uri = "/stream",
    .method = HTTP_GET,
    .handler = stream_handler,
    .user_ctx = NULL
  };

  if (httpd_start(&stream_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(stream_httpd, &stream_uri);
    Serial.println("📺 Stream MJPEG đang chạy tại /stream");
  } else {
    Serial.println("❌ Không thể khởi động stream MJPEG");
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("🚀 Bắt đầu");

  // Cấu hình camera
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 12;
  config.fb_count = 2;
  config.fb_location = CAMERA_FB_IN_PSRAM;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("❌ Camera init failed");
    while (1);
  }

  // Kết nối WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.print("\n✅ IP: "); Serial.println(WiFi.localIP());

  // Web server
  server.on("/", handleRoot);
  server.on("/capture", handleCapture);
  server.begin();
  Serial.println("🌐 Web server chạy tại /");

  startCameraStream();
}

void loop() {
  server.handleClient();
}
