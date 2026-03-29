#include <Servo.h>

// Define your Servo Pins
const int pinPan = 9;   // Horizontal Servo
const int pinTilt = 10;  // Vertical Servo

Servo servoPan;
Servo servoTilt;

// Servo Center Positions
int panPos = 90;
int tiltPos = 90;

// Camera Resolution (must match Python script)
const int stageWidth = 640;
const int stageHeight = 480;

void setup() {
  Serial.begin(9600);
  
  servoPan.attach(pinPan);
  servoTilt.attach(pinTilt);
  
  // Move to center on start
  servoPan.write(panPos);
  servoTilt.write(tiltPos);
}

void loop() {
  if (Serial.available() > 0) {
    // Read the incoming string until newline
    String data = Serial.readStringUntil('\n');
    
    // Find the comma index
    int commaIndex = data.indexOf(',');
    
    if (commaIndex > 0) {
      // Parse X and Y
      int targetX = data.substring(0, commaIndex).toInt();
      int targetY = data.substring(commaIndex + 1).toInt();
      
      // Map pixel coordinates to Servo degrees (0-180)
      // Mirroring: Change (0, 180) to (180, 0) if servos move in wrong direction
      int targetPan = map(targetX, 0, stageWidth, 180, 0); 
      int targetTilt = map(targetY, 0, stageHeight, 0, 180);
      
      // Move Servos
      servoPan.write(targetPan);
      servoTilt.write(targetTilt);
    }
  }
}

// Built-in LED on most Arduinos is on Pin 13
// const int ledPin = 13;
// unsigned long lastReceivedTime = 0;
// const long timeout = 500; // Turn off if no data for 0.5 seconds

// void setup() {
//   Serial.begin(9600);
//   pinMode(ledPin, OUTPUT);
//   digitalWrite(ledPin, LOW); // Start with LED off
//   Serial.println("Arduino Ready: Waiting for coordinates...");
// }

// void loop() {
//   // Check if data is incoming
//   if (Serial.available() > 0) {
//     // Read the data to clear the buffer
//     String data = Serial.readStringUntil('\n');
    
//     // Quick validation: Check for the comma
//     if (data.indexOf(',') > 0) {
//       digitalWrite(ledPin, HIGH); // Turn LED ON
//       lastReceivedTime = millis(); // Update the "last seen" timer
//     }
//   }

//   // Auto-timeout: Turn off LED if connection goes quiet
//   if (millis() - lastReceivedTime > timeout) {
//     digitalWrite(ledPin, LOW);
//   }
// }
