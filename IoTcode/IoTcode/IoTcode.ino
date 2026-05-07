#include <ESP8266WiFi.h>
#include <FirebaseESP8266.h>
#include <WiFiClientSecure.h>
#include <ESP8266HTTPClient.h>

#define WIFI_SSID ""          
#define WIFI_PASSWORD ""    

#define API_KEY "" 
#define FIREBASE_HOST ""

#define trigPin D1
#define echoPin D2
#define ledPin D4

FirebaseData firebaseData;
FirebaseConfig config;
FirebaseAuth auth;
FirebaseJson json;

double initDistance = 0;
double maxTolerance = 15.0;
double prevProzent = -1;
unsigned long lastSentTime = -1;
const unsigned long SEND_INTERVAL = 3600000; // In each hour
bool isLidRecentlyOpened = false;
String googleScriptUrl = "";
bool mailSent = false;

double measureHeight();
double getAverageDistance(int amount);
void updateLedStatus(double percent);
void sendLidIncrement();

void setup() {
  
  Serial.begin(9600);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(ledPin, OUTPUT);
  // 1. WI-FI Connection
  Serial.println("Connecting to Wi-Fi");
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int time = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.println("...");
    time++;
    if(time > 40) {
      Serial.println("Connection Timeout, Resetting...");
      ESP.restart();
    }
  }
  Serial.println("\nWi-Fi Connection Established!");
  Serial.print("IP Adress: ");
  Serial.println(WiFi.localIP());
  Serial.print("RSSI: ");
  Serial.println(WiFi.RSSI());

  // 2. FIREBASE Connection
  config.host = FIREBASE_HOST;
  config.signer.tokens.legacy_token = API_KEY;
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  Serial.println("System Starting... Calibrating");
  delay(100);

  initDistance = getAverageDistance(10);
  if(initDistance == 0) {
    Serial.println("Calibration Error!");
    while(true) {
      digitalWrite(ledPin, LOW);
      delay(100);
      digitalWrite(ledPin, HIGH);
      delay(100);
    }
  }
  
  Serial.print("Calibration Succesfull, Depth: ");
  Serial.print(initDistance);
  Serial.println(" cm.");

  Firebase.setDouble(firebaseData, "/smart_trash_bin/config/depth", initDistance);
}

void loop() {

  if(Firebase.getString(firebaseData, "/smart_trash_bin/control/measure_command")) {
    if(firebaseData.stringData() == "MEASURE") {
      Serial.println("Web requested measuring.");
      double currentRequestedDistance = getAverageDistance(5);
      int fillProzent = calculatePercent(currentRequestedDistance);
      json.clear();
      json.set("fillPercent", fillProzent);
      json.set("isCriticalLevel", (fillProzent >= 80));
      json.set("lastUpdated/.sv", "timestamp");
      Firebase.updateNode(firebaseData, "/smart_trash_bin/live_data", json);
      Serial.println("Updated the current percent, because of web request");
    }
    Firebase.setString(firebaseData, "/smart_trash_bin/control/measure_command", "IDLE");
  }

  double currentDistance = getAverageDistance(5);
  if(currentDistance == 0) {
    Serial.println("Error durig measuring!");
    return;
  }

  int fillProzent = calculatePercent(currentDistance);

  Serial.print("%");
  Serial.print(fillProzent);
  Serial.println(" filled");

  bool isFirstRun = (prevProzent == -1);
  bool isBigChange = (abs(prevProzent - fillProzent) >= 5);
  bool isTimeUp = (millis() - lastSentTime > SEND_INTERVAL);

  if(isFirstRun || isBigChange || isTimeUp) {
    Serial.println(" -> Sending Update to Cloud...");
    json.clear();
    json.set("fillPercent", fillProzent);
    json.set("isCriticalLevel", (fillProzent >= 80));
    json.set("lastUpdated/.sv", "timestamp");

    if(Firebase.updateNode(firebaseData, "/smart_trash_bin/live_data", json)) {
      prevProzent = fillProzent;
      lastSentTime = millis();
    } else {
      Serial.print("Error: "); Serial.println(firebaseData.errorReason());
    }
  }
  updateLedStatus(fillProzent);
  delay(1000);
}


double measureHeight() {
//Clear Sensor
  digitalWrite(trigPin, LOW); delay(2);
//Trigger
  digitalWrite(trigPin, HIGH); delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
//Measuring
  long time = pulseIn(echoPin, HIGH, 40000);
  double distance = time * 0.034 / 2;

  if(time == 0) {
    Serial.println("Distance could not be measured!");
    return -1;
  }
  else return distance;
}

double getAverageDistance(int amount) {
  double total = 0;
  int valid = 0;
  double lastValidMeasurement = -1;
  double currentMaxLimit = (initDistance == 0) ? 60.0 : (initDistance + maxTolerance);

  for(int i = 0; i < (amount + 10); i++) {
    double measure = measureHeight();

    if(measure <= 0 || measure > currentMaxLimit) {
      Serial.println("Lid is opened (or Error occured)");
      if(isLidRecentlyOpened == false) {
        sendLidIncrement();
        isLidRecentlyOpened = true;
      }
      delay(3000);
      continue;
    }
    if(isLidRecentlyOpened == true) {
      Serial.println("To avoid missmeasurings, applying 10 second delay after lid is closed");
      delay(10000);
      isLidRecentlyOpened = false;
      Serial.println("Lid is closed, System is back to the normal(or Error vanished)");
    }

    if(lastValidMeasurement == -1) {
        total += measure;
        lastValidMeasurement = measure;
        valid++;
    } else {
      double diff = abs(measure - lastValidMeasurement);
      double limit = lastValidMeasurement * 0.20;
      if(diff <= limit) {
        total += measure;
        lastValidMeasurement = measure;
        valid++;
      }
    }
    if(valid == amount) break;
    delay(30);
  }
  if(valid < amount) return 0;

  return total / valid;
}

void updateLedStatus(double percent) {
 digitalWrite(ledPin, (percent >= 80) ? LOW : HIGH);
}

void sendLidIncrement() {
  int currentCount = 0;
  String path = "/smart_trash_bin/stats/lid_open_count";
  if (Firebase.getInt(firebaseData, path)) {
    currentCount = firebaseData.intData();
  } else {
    currentCount = 0;
  }
  int newCount = currentCount + 1;
  if(Firebase.setInt(firebaseData, path, newCount)) {
    Serial.println("Lid counter is succesfully icnremented and sended to cloud");
  } else {
    Serial.print("Error during incrementing the lid count: "); Serial.println(firebaseData.errorReason());
  }
}

int calculatePercent(double currentDistance) {
  double fillProzent =  int((1 - (currentDistance / initDistance)) * 100);
  if(fillProzent < 0) fillProzent = 0;
  else if(fillProzent > 100) fillProzent = 100;
  if(fillProzent >= 80 && mailSent == false) {
    sendEmailNotification();
    mailSent = true;
  }
  if(fillProzent < 80) {
    mailSent = false;
  }
  return fillProzent;
}

void sendEmailNotification() {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClientSecure client;
    client.setInsecure();
    HTTPClient http;

    Serial.println("Sending Mail...");
    http.begin(client, googleScriptUrl);

    int httpCode = http.GET();

    if(httpCode > 0) {
      Serial.println("Mail triggered succesfully");
    } else {
      Serial.print("Error during triggering the mail"); Serial.println(http.errorToString(httpCode));
    }
    http.end();
  }
}