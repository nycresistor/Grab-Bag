const static int clock_pin = 2;
const static int data_pin = 3;

const static int columns = 60;
const static int modules = 6;
const static int rows = 7;
const static int row_pin[rows] = { 7,8,9,10,11,12,13 };

static int active_row = -1;

#include <avr/pgmspace.h>
#include "hfont.h"

// Resources:
// 256K program space
// 8K RAM
uint8_t b1[columns*modules];
uint8_t b2[columns*modules];

class Bitmap {
  uint8_t* data;
  uint8_t* dpl;
public:
  Bitmap() {
    data = b1;
    dpl = b2;
  }
  void erase() {
    for (int i = 0; i < columns*modules; i++) data[i] = 0;
  }
  void writeStr(char* p, int x, int y) {
    while (*p != '\0') {
      x = writeChar(*p,x,0);
      p++;
      x++;
    }
  }

  int writeChar(char c, int x, int y) {
    int coff = (int)c * 8;
    uint8_t row = pgm_read_byte(charData+coff);
    if (row == 0) {
      return x;
    }    
    uint8_t mask = 0xfe >> y;
    while (row != 1) {
      row = row >> y;
      data[x] = row | (data[x] & mask);
      coff++;
      x++;
      row = pgm_read_byte(charData+coff);
    }
    return x;
  }
  void flip() {
    cli();
    uint8_t* tmp = data;
    data = dpl;
    dpl = tmp;
    sei();
  }
  uint8_t* getDisplay() { return dpl; }
};

static Bitmap b;

void rowOff() {
  if (active_row >= 0) {
    digitalWrite(row_pin[active_row],LOW);
    active_row = -1;
  }
}

void rowOn(int row) {
  active_row = row;
  if (active_row >= 0) { 
    digitalWrite(row_pin[active_row],HIGH);
  }
}

void shiftIn(bool bit) {
  digitalWrite(data_pin, bit?HIGH:LOW);
  digitalWrite(clock_pin, LOW);
  digitalWrite(clock_pin, HIGH);
}

void setup() {
  b.erase();
  b.writeStr("FUCK YOU",5,0);
  b.flip();
  b.erase();
  b.writeStr("GAAAH",5,0);
  //b.flip();
  pinMode(data_pin, OUTPUT);
  digitalWrite(data_pin, HIGH);
  pinMode(clock_pin, OUTPUT);
  digitalWrite(clock_pin, HIGH);
  for (int i =0; i < rows; i++) {
    pinMode(row_pin[i], OUTPUT);
    digitalWrite(row_pin[i], HIGH);
  }
  // 2ms per row/interrupt
  // clock: 16MHz
  // target: 500Hz
  // 32000 cycles per interrupt
  // Prescaler: 1/64 OC: 500
  // CS[2:0] = 0b011
  // WGM[3:0] = 0b0100 CTC mode (top is OCR3A)
  
  OCR3A = 500;
  TCCR3A = 0b00000000;
  TCCR3B = 0b00001011;
  TIMSK3 = _BV(OCIE3A);
  
}

static unsigned int curRow = 0;

void loop() {
  delay(1000);
  b.flip();
}

ISR(TIMER3_COMPA_vect)
{
  uint8_t row = curRow % 7;
  uint8_t mask = 1 << (7-row);
  uint8_t* p = b.getDisplay();
  rowOff();
  for (int i = 0; i < 60; i++) {
    // clock is 2, data is 3
    // 2 == E4, 3 == E5 on the mega
    if ( (p[60-i] & mask) != 0 ) {
      PORTE = _BV(4) | _BV(5);
      PORTE = _BV(5);
    } else {
      PORTE = _BV(4);
      PORTE = 0;
    }
    //PORTE = _BV(4);
  //    digitalWrite(clock_pin, LOW);
  //  digitalWrite(clock_pin, HIGH);
  }
  rowOn(curRow%7);
  curRow++;
}

