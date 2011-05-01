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
 * */

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
  pinMode(D_pin,OUTPUT);  Serial.begin(serial_speed);
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

int temp_sp = -1;
int temp_mv = 0;
unsigned long last_temp_ms = 0;
const unsigned long temp_interval_ms = 2000;

void measure_temp() {
  int raw = analogRead(analog_thermistor_pin);
  temp_mv = thermistorToCelsius(raw);
  Serial.print("Raw value ");
  Serial.print(raw);
  Serial.print(", temp ");
  Serial.println(temp_mv);
}


void do_temperature() {
  if (millis() < last_temp_ms + temp_interval_ms) return;
  last_temp_ms = millis();
  measure_temp();
  if (temp_sp < 0) {
    digitalWrite(relay_pin, LOW);
    return;
  }
  digitalWrite(relay_pin, (temp_mv < temp_sp)?HIGH:LOW);
}

const int buf_size = 64;
char line_buf[buf_size];
int buf_idx = 0;

void do_command() {
  String command(line_buf);
  if (command.equals("stop")) { elevatorOff(); }
  else if (command.equals("down")) { elevatorDown(); }
  else if (command.equals("up")) { elevatorUp(); }
  else if (command.startsWith("temp ")) {
    String setting = command.substring(5);
    if (setting.equals("off")) {
      temp_sp = -1;
    } else {
      temp_sp = atoi(line_buf+5);
    }
    Serial.print("Set point at ");
    Serial.println(temp_sp);
  }
}

void loop() {
  do_temperature();
  while (1) {
    int inchr = Serial.read();
    if (inchr == -1) break;
    if (inchr == '\n' || inchr == '\r') {
      line_buf[buf_idx] = '\0';
      buf_idx = 0;
      do_command();
    } else {
      line_buf[buf_idx++] = inchr;
      if (buf_idx >= buf_size -1) { buf_idx = buf_size - 1; }
    }
  }
}

