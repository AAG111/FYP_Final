/*

  Wiring
  ESP32-C3 GPIO 4 (A4) → TFT CLK
  ESP32-C3 GPIO 6      → TFT MOSI
  ESP32-C3 GPIO 5 (A5) → TFT MISO
  ESP32-C3 GPIO 7      → TFT CS
  ESP32-C3 GPIO 2 (A2) → TFT DC
  ESP32-C3 GPIO 3 (A3) → TFT RST
  ESP32-C3 3.3V        → TFT VCC
  ESP32-C3 GND         → TFT GND
  ESP32-C3 3.3V        → TFT LED
  
  Edit only lines 25-27 (WiFi + server IP)
*/

#include <TFT_eSPI.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ═══════════════════════════════════════════════════════════════
// Configuration - EDIT THESE 3 LINES ONLY
// ═══════════════════════════════════════════════════════════════

const char* ssid = "WIFI_SSID";              // ← CHANGE
const char* password = "WIFI_PASSWORD";      // ← CHANGE
const char* flaskServerUrl = "http://192.168.0.165:5000";  // ← CHANGE to your laptop IP

// ═══════════════════════════════════════════════════════════════
// ESP32-C3 Pin Configuration (DO NOT CHANGE - Hardware optimized)
// ═══════════════════════════════════════════════════════════════

// SPI Pins (Fixed on ESP32-C3)
#define TFT_CLK   4      // GPIO 4 (A4)  - SPI Clock
#define TFT_MOSI  6      // GPIO 6       - SPI Data In
#define TFT_MISO  5      // GPIO 5 (A5)  - SPI Data Out

// Control Pins
#define TFT_CS    7      // GPIO 7       - Chip Select
#define TFT_DC    2      // GPIO 2 (A2)  - Data/Command
#define TFT_RST   3      // GPIO 3 (A3)  - Reset

// ═══════════════════════════════════════════════════════════════
// TFT Display Setup
// ═══════════════════════════════════════════════════════════════

TFT_eSPI tft = TFT_eSPI();

// ═══════════════════════════════════════════════════════════════
// Data Structure
// ═══════════════════════════════════════════════════════════════

struct FormData {
  String exercise;
  int formScore;
  float leftKnee;
  float rightKnee;
  float heartRate;
  float stress;
  String feedback;
  unsigned long timestamp;
};

FormData currentFormData = {"STANDING", 0, 0, 0, 0, 0, "Initializing...", 0};

// ═══════════════════════════════════════════════════════════════
// WiFi Setup
// ═══════════════════════════════════════════════════════════════

void setupWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  Serial.println();
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("✓ WiFi Connected!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    
    // Show on TFT
    tft.fillScreen(TFT_BLACK);
    tft.setTextColor(TFT_GREEN, TFT_BLACK);
    tft.setTextSize(2);
    tft.drawString("WiFi Connected!", 30, 110);
    tft.setTextSize(1);
    tft.drawString(WiFi.localIP().toString().c_str(), 50, 130);
    delay(2000);
  } else {
    Serial.println("✗ WiFi Connection Failed!");
    tft.fillScreen(TFT_BLACK);
    tft.setTextColor(TFT_RED, TFT_BLACK);
    tft.setTextSize(2);
    tft.drawString("WiFi Failed!", 50, 110);
  }
}

// ═══════════════════════════════════════════════════════════════
// Fetch Dashboard Data from Flask Server
// ═══════════════════════════════════════════════════════════════

bool fetchDashboardData() {
  if (WiFi.status() != WL_CONNECTED) {
    return false;
  }
  
  HTTPClient http;
  String dashboardUrl = String(flaskServerUrl) + "/api/tft/dashboard";
  
  http.begin(dashboardUrl);
  int httpCode = http.GET();
  
  if (httpCode == 200) {
    String payload = http.getString();
    
    // Parse JSON response
    StaticJsonDocument<500> doc;
    DeserializationError error = deserializeJson(doc, payload);
    
    if (!error) {
      JsonObject analysis = doc["analysis"];
      JsonObject sensors = doc["sensors"];
      
      // Extract analysis data
      currentFormData.exercise = analysis["exercise"] | "STANDING";
      currentFormData.formScore = analysis["form_score"] | 0;
      currentFormData.feedback = analysis["feedback"] | "Waiting...";
      
      // Extract angles
      if (analysis.containsKey("angles")) {
        currentFormData.leftKnee = analysis["angles"]["left_knee"] | 0;
        currentFormData.rightKnee = analysis["angles"]["right_knee"] | 0;
      }
      
      // Extract sensor data
      currentFormData.heartRate = sensors["heart_rate"] | 0;
      currentFormData.stress = sensors["stress"] | 0;
      
      currentFormData.timestamp = millis();
      
      http.end();
      return true;
    }
  }
  
  http.end();
  return false;
}

// ═══════════════════════════════════════════════════════════════
// Display Dashboard on TFT
// ═══════════════════════════════════════════════════════════════

void displayDashboard() {
  // Clear screen
  tft.fillScreen(TFT_BLACK);
  
  // Title bar
  tft.fillRect(0, 0, 320, 30, TFT_DARKGREY);
  tft.setTextColor(TFT_WHITE, TFT_DARKGREY);
  tft.setTextSize(2);
  tft.drawString("FormCheck", 100, 8);
  
  // Exercise Type
  tft.setTextColor(TFT_CYAN, TFT_BLACK);
  tft.setTextSize(2);
  tft.drawString("Exercise:", 10, 40);
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.drawString(currentFormData.exercise.c_str(), 130, 40);
  
  // Form Score - Color coded
  uint16_t scoreColor;
  if (currentFormData.formScore >= 80) {
    scoreColor = TFT_GREEN;
  } else if (currentFormData.formScore >= 60) {
    scoreColor = TFT_YELLOW;
  } else {
    scoreColor = TFT_RED;
  }
  
  tft.setTextColor(TFT_CYAN, TFT_BLACK);
  tft.setTextSize(2);
  tft.drawString("Form:", 10, 70);
  tft.setTextColor(scoreColor, TFT_BLACK);
  tft.setTextSize(3);
  String scoreStr = String(currentFormData.formScore) + "%";
  tft.drawString(scoreStr.c_str(), 190, 65);
  
  // Heart Rate
  tft.setTextColor(TFT_CYAN, TFT_BLACK);
  tft.setTextSize(1);
  tft.drawString("HR:", 10, 105);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  String hrStr = String((int)currentFormData.heartRate) + " BPM";
  tft.drawString(hrStr.c_str(), 35, 105);
  
  // Stress Level - Color coded
  uint16_t stressColor;
  if (currentFormData.stress < 40) {
    stressColor = TFT_GREEN;
  } else if (currentFormData.stress < 70) {
    stressColor = TFT_YELLOW;
  } else {
    stressColor = TFT_RED;
  }
  
  tft.setTextColor(TFT_CYAN, TFT_BLACK);
  tft.drawString("Stress:", 160, 105);
  tft.setTextColor(stressColor, TFT_BLACK);
  String stressStr = String((int)currentFormData.stress) + "%";
  tft.drawString(stressStr.c_str(), 220, 105);
  
  // Joint Angles
  tft.setTextColor(TFT_CYAN, TFT_BLACK);
  tft.setTextSize(1);
  tft.drawString("Left Knee:", 10, 125);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString(String(currentFormData.leftKnee, 1).c_str(), 75, 125);
  
  tft.setTextColor(TFT_CYAN, TFT_BLACK);
  tft.drawString("Right Knee:", 160, 125);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString(String(currentFormData.rightKnee, 1).c_str(), 235, 125);
  
  // Feedback
  tft.setTextColor(TFT_GREEN, TFT_BLACK);
  tft.setTextSize(1);
  tft.drawString("Feedback:", 10, 145);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString(currentFormData.feedback.c_str(), 10, 160);
  
  // Status Bar at Bottom
  tft.fillRect(0, 220, 320, 20, TFT_DARKGREY);
  tft.setTextColor(TFT_WHITE, TFT_DARKGREY);
  tft.setTextSize(1);
  
  unsigned long secondsAgo = (millis() - currentFormData.timestamp) / 1000;
  String status = "Connected - Last: " + String(secondsAgo) + "s ago";
  tft.drawString(status.c_str(), 5, 223);
}

// ═══════════════════════════════════════════════════════════════
// Setup TFT Display
// ═══════════════════════════════════════════════════════════════

void setupTFT() {
  tft.init();
  tft.setRotation(1);  // Landscape
  tft.fillScreen(TFT_BLACK);
  
  // Splash screen
  tft.setTextColor(TFT_GREEN, TFT_BLACK);
  tft.setTextSize(2);
  tft.drawString("FormCheck", 90, 50);
  tft.drawString("ESP32-C3", 90, 80);
  
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextSize(1);
  tft.drawString("Initializing...", 120, 110);
  
  delay(2000);
}

// ═══════════════════════════════════════════════════════════════
// Setup
// ═══════════════════════════════════════════════════════════════

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n╔═══════════════════════════════════════╗");
  Serial.println("║  FormCheck - ESP32-C3 TFT Display   ║");
  Serial.println("║  (Optimized for ESP32-C3)           ║");
  Serial.println("╚═══════════════════════════════════════╝\n");
  
  // Setup TFT
  Serial.println("Initializing TFT display...");
  setupTFT();
  
  // Setup WiFi
  Serial.println("Setting up WiFi...");
  setupWiFi();
  
  Serial.println("✓ Setup complete! Starting main loop...\n");
  Serial.println("Pin Configuration (ESP32-C3):");
  Serial.println("  GPIO 4 (A4) = CLK");
  Serial.println("  GPIO 6      = MOSI");
  Serial.println("  GPIO 5 (A5) = MISO");
  Serial.println("  GPIO 7      = CS");
  Serial.println("  GPIO 2 (A2) = DC");
  Serial.println("  GPIO 3 (A3) = RST");
  Serial.println();
}

// ═══════════════════════════════════════════════════════════════
// Main Loop
// ═══════════════════════════════════════════════════════════════

unsigned long lastUpdate = 0;
const unsigned long UPDATE_INTERVAL = 2000;  // Update every 2 seconds

void loop() {
  // Fetch data periodically
  if (millis() - lastUpdate > UPDATE_INTERVAL) {
    lastUpdate = millis();
    
    Serial.print("Fetching data from Flask server... ");
    
    if (fetchDashboardData()) {
      Serial.println("✓ Success");
    } else {
      Serial.println("✗ Failed");
      currentFormData.feedback = "No connection";
    }
  }
  
  // Display dashboard
  displayDashboard();
  
  delay(100);
}
