const int ALERT_LED_PIN = 32;

void setup() {
  Serial.begin(115200);
  pinMode(ALERT_LED_PIN, OUTPUT);
  digitalWrite(ALERT_LED_PIN, LOW);
  Serial.println("Alert LED Test Initialized");
}

void loop() {
  Serial.println("Alert LED Flash");
  digitalWrite(ALERT_LED_PIN, HIGH);
  delay(200); // 200ms ON
  digitalWrite(ALERT_LED_PIN, LOW);
  
  delay(2000); // Wait 2s
}
