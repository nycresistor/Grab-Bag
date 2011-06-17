/*
  Blink
  Turns on an LED on for one second, then off for one second, repeatedly.
 
  This example code is in the public domain.
 */

#define LED_COL_CNT 7
int led_col[LED_COL_CNT] = { 
  // on LO module: 
  // 2, 3, 4, 5, 6, 7, 8
  // on uno32:
  13, 12, 11, 10, 9, 8, 41
};

#define ROW_CNT 4

int row[ROW_CNT] = {
  // on LO module:
  // 9, 10, 11, 12
  // on uno32:
  40, 39, 38, 37
};

void setup() {                
  // initialize the digital pin as an output.
  // Pin 13 has an LED connected on most Arduino boards:
  pinMode(13, OUTPUT);
  for (int i = 0; i < LED_COL_CNT; i++) {
    pinMode(led_col[i], OUTPUT);
    digitalWrite(led_col[i], HIGH);
  }
  for (int i = 0; i < ROW_CNT; i++) {
    pinMode(row[i], OUTPUT);
    digitalWrite(row[i], HIGH);
  }
  digitalWrite(led_col[3], LOW);
  digitalWrite(row[1], LOW);
  
}

void loop() {
  digitalWrite(13, HIGH);   // set the LED on
  delay(1000);              // wait for a second
  digitalWrite(13, LOW);    // set the LED off
  delay(1000);              // wait for a second
}
