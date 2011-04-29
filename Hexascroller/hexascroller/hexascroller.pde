// CLOCK PIN: A0 (22)
// DATA 1: A1 (23)
// DATA 2: A2 (24)
// DATA 3: A3 (25)

// ROW 0: E4 (2)
// ROW 1: E5 (3)
// ROW 2: E3 (5)
// ROW 3: H3 (6)
// ROW 4: H4 (7)
// ROW 5: H5 (8)
// ROW 6: H6 (9)

const static int columns = 120;
const static int modules = 3;
const static int rows = 7;

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

inline void rowOff() {
  PORTE &= ~(_BV(4) | _BV(5) | _BV(3));
  PORTH &= ~(_BV(3) | _BV(4) | _BV(5) | _BV(6));
}

inline void rowOn(int row) {
  // ROW 0: E4 (2)
  // ROW 1: E5 (3)
  // ROW 2: E3 (5)
  // ROW 3: H3 (6)
  // ROW 4: H4 (7)
  // ROW 5: H5 (8)
  // ROW 6: H6 (9)
  switch( row ) {
    case 0: PORTE |= _BV(4); break;
    case 1: PORTE |= _BV(5); break;
    case 2: PORTE |= _BV(3); break;
    case 3: PORTH |= _BV(3); break;
    case 4: PORTH |= _BV(4); break;
    case 5: PORTH |= _BV(5); break;
    case 6: PORTH |= _BV(6); break;
  }
}

void setup() {
  b.erase();
  b.writeStr("SPANDEX AND",5,0);
  b.flip();
  b.erase();
  b.writeStr("HOT DOGS",5,0);
  //b.flip();
  // CLOCK PIN: A0
  // DATA 1: A1
  // DATA 2: A2
  // DATA 3: A3
  DDRA = 0x0f;
  PORTA = 0x0f;
// ROW 0: E4 (2)
// ROW 1: E5 (4)
// ROW 2: E3 (5)
// ROW 3: H3 (6)
// ROW 4: H4 (7)
// ROW 5: H5 (8)
// ROW 6: H6 (9)
  DDRE |= _BV(4) | _BV(5) | _BV(3);
  DDRH |= _BV(3) | _BV(4) | _BV(5) | _BV(6);
  PORTE &= ~(_BV(4) | _BV(5) | _BV(3));
  PORTH &= ~(_BV(3) | _BV(4) | _BV(5) | _BV(6));
  // 2ms per row/interrupt
  // clock: 16MHz
  // target: 500Hz
  // 32000 cycles per interrupt
  // Prescaler: 1/64 OC: 500
  // CS[2:0] = 0b011
  // WGM[3:0] = 0b0100 CTC mode (top is OCR3A)
  
  TCCR3A = 0b00000000;
  TCCR3B = 0b00001011;
  TIMSK3 = _BV(OCIE3A);
  OCR3A = 400;
  
  delay(500);
}

static unsigned int curRow = 0;

static int xoff = 0;
void loop() {
  delay(30);
  b.erase();
  b.writeStr("HOT DOGS",xoff,0);
  xoff++;
  xoff = xoff % 120;
  b.flip();
}

ISR(TIMER3_COMPA_vect)
{
  uint8_t row = curRow % 7;
  uint8_t mask = 1 << (7-row);
  uint8_t* p = b.getDisplay();
  rowOff();
  for (int i = 0; i < columns; i++) {
    // clock is 2, data is 3
    // 2 == E4, 3 == E5 on the mega
    if ( (p[(columns-1)-i] & mask) != 0 ) {
      //PORTE = _BV(4);
      //PORTA = 1;
      //PORTE = 0;
      PORTA = _BV(0) | _BV(1);
      PORTA = _BV(1);
    } else {
      //PORTE = _BV(4);
      //PORTA = 0;
      //PORTE = 0;
      PORTA = _BV(0);
      PORTA = 0;
    }

    PORTA |= _BV(0);
    //PORTE = _BV(4);
  //    digitalWrite(clock_pin, LOW);
  //  digitalWrite(clock_pin, HIGH);
  }
  rowOn(curRow%7);
  curRow++;
}

