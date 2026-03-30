#include <Servo.h>

// Define your Servo Pins
const int pinPan = 9;   
const int pinTilt = 10;
const int signalPin = 11;   // Output pin

Servo servoPan;
Servo servoTilt;

// Servo Center Positions
int panPos = 90;
int tiltPos = 0;

// Camera Resolution
const int stageWidth = 640;
const int stageHeight = 480;

// Timeout variables
unsigned long lastReceivedTime = 0;
const long timeout = 500; // 0.5 seconds

void setup() {
  Serial.begin(9600);

  servoPan.attach(pinPan);
  servoTilt.attach(pinTilt);

  pinMode(signalPin, OUTPUT);
  digitalWrite(signalPin, LOW);

  servoPan.write(panPos);
  servoTilt.write(tiltPos);
}

void loop() {

  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');
    int commaIndex = data.indexOf(',');

    if (commaIndex > 0) {
      int targetX = data.substring(0, commaIndex).toInt();
      int targetY = data.substring(commaIndex + 1).toInt();

      int targetPan = map(targetX, 0, stageWidth, 180, 0);
      int targetTilt = map(targetY, 0, stageHeight, 0, 180)-90;

      servoPan.write(targetPan);
      servoTilt.write(targetTilt);

      digitalWrite(signalPin, HIGH);     // Face detected
      lastReceivedTime = millis();       // Update timer
    }
  }

  // If no data for some time → turn OFF
  if (millis() - lastReceivedTime > timeout) {
    digitalWrite(signalPin, LOW);
  }
}