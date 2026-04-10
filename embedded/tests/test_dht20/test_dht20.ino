#include "DHT20.h"
#include <Wire.h>

DHT20 dht;

void setup() {
  Serial.begin(115200);
  delay(1500);

  Wire.begin();
  dht.begin();
  Serial.println("DHT20 Test Initialized!");
}

void loop() {
  int status = dht.read();

  if (status != DHT20_OK) {
    Serial.print("Failed to read from DHT20 sensor! Error: ");
    Serial.println(status);
  } else {
    Serial.print("Temperature: ");
    Serial.print(dht.getTemperature(), 1);
    Serial.println(" °C");
    Serial.print("Humidity: ");
    Serial.print(dht.getHumidity(), 1);
    Serial.println(" %");
  }
  delay(2000);
}