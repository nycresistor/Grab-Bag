#include "ThermistorTable.h"


/**
 * H-bridge diagram
 *
 *            VCC
 *             |
 *  A  --P-----+-----P--  B
 *       |           |
 *       +--- MTR ---+
 *       |           |
 *  C  --N-----+-----N--  D
 *             |
 *            GND
 *
 * OFF: A high, B high, C low, D low
 * FWD: A low, B high, C low, D high
 * BCK: A high, B low, C high, D low
 *
 * Colors: Yellow = A, Orange = B, Brown = C, Blue = D
 *
 */

static const int A_pin = 2;
static const int B_pin = 3;
static const int C_pin = 4;
static const int D_pin = 5;
 
static const int relay_pin = 7;

static const int analog_thermistor_pin = 0;

static const int serial_speed = 9600;

void setup() {
  digitalWrite(relay_pin,LOW);
  pinMode(relay_pin,OUTPUT);
  // Set up h-bridge
  elevatorOff();
  pinMode(A_pin,OUTPUT);
  pinMode(B_pin,OUTPUT);
  pinMode(C_pin,OUTPUT);
  pinMode(D_pin,OUTPUT);
  Serial.begin(serial_speed);
  Serial.println("Egg Preparation System Model A initialized.");
}

void elevatorOff() {
  Serial.println("elevator off");
  digitalWrite(A_pin,HIGH);
  digitalWrite(B_pin,HIGH);
  digitalWrite(C_pin,LOW);
  digitalWrite(D_pin,LOW);
}

void elevatorDown() {
  Serial.println("elevator down");
  digitalWrite(A_pin,LOW);
  digitalWrite(B_pin,HIGH);
  digitalWrite(C_pin,LOW);
  digitalWrite(D_pin,HIGH);
}

void elevatorUp() {
  Serial.println("elevator up");
  digitalWrite(A_pin,HIGH);
  digitalWrite(B_pin,LOW);
  digitalWrite(C_pin,HIGH);
  digitalWrite(D_pin,LOW);
}

void loop() {
  int raw = analogRead(analog_thermistor_pin);
  int temp = thermistorToCelsius(raw);
  Serial.print("Raw value ");
  Serial.print(raw);
  Serial.print(", temp ");
  Serial.println(temp);
  delay(2000);
  digitalWrite(relay_pin, (temp<5)?HIGH:LOW);
  int inchr = Serial.read();
  if (inchr == 's') elevatorOff();
  if (inchr == 'f') elevatorDown();
  if (inchr == 'b') elevatorUp();
}

