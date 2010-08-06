#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <string.h>
#include <stdint.h>
#define F_CPU 12000000UL  // 12 MHz

#define SET_OUTPUT(P,B) { DDR##P |= _BV(B); }
#define SET_INPUT(P,B) { DDR##P &= ~_BV(B); }

#define SET_PIN(P,B) { PORT##P |= _BV(B); }
#define CLR_PIN(P,B) { PORT##P &= ~_BV(B); }

#define GET_PIN(P,B) ((PIN##P & _BV(B)) != 0)

#define DIGIT_COUNT 4

#define INITIAL_HOURS 504L

// Number of deciseconds remaining in the test
volatile int32_t deciRemaining = INITIAL_HOURS * 60L * 60L * 10L;
volatile bool paused = true;

char digits[10] = {
  0x77, 0x24,
  0x5d, 0x6d,
  0x2e, 0x6b,
  0x7b, 0x25,
  0x7f, 0x2f
};

// The shift registers max out at 3MHz, so we need ~4 nops per cycle to
// be on the safe side.  That, plus possible call overhead, should ensure
// it works.
void nops() {
  asm volatile("nop\n\t"
	       "nop\n\t"
	       "nop\n\t"
	       "nop\n\t"
	       ::);
}

void initClock()
{
  // using 16-bit timer 1 with prescaler clock / 64.
  // 18750 clock pulses per 1/10th second.
  // Reset on OCR1A match.
  // WGM1: 0100  CS1: 011
  TCCR1A = 0x00;
  TCCR1B = 0x0a;
  TCCR1C = 0x00; // not using the force matches

  OCR1A = 18750;

  TIMSK1 = 0x02; // turn on interrupt
}

void initPins()
{
  SET_OUTPUT(C,5);  // CLK
  SET_OUTPUT(C,4);  // DATA
  SET_OUTPUT(C,3);  // OE
  SET_OUTPUT(C,2);  // LE
}


void initButtons()
{
  // D5 - PCINT21   --|
  // D6 - PCINT22     |-- PCI2
  // D7 - PCINT23   --|
  // B0 - PCINT0    ----- PCI0
  SET_INPUT(D,5); // Set button pins as inputs
  SET_INPUT(D,6);
  SET_INPUT(D,7);
  SET_INPUT(B,0);
  SET_PIN(D,5); // Pull-up resistors on
  SET_PIN(D,6);
  SET_PIN(D,7);
  SET_PIN(B,0);
  PCMSK2 = 0xe0;
  PCMSK0 = 0x01;
  PCICR = 0x05;
}

void init()
{
  cli();
  initPins();
  initButtons();
  initClock();
  set_sleep_mode( SLEEP_MODE_IDLE );
  sei();
}

void start_shift() {
  nops();
}

void end_shift() {
  CLR_PIN(C,3); // OE low to turn on drivers
  SET_PIN(C,2); // LE is high (passing data)
  SET_PIN(C,5); // clock high (propegation)
  CLR_PIN(C,2); // LE is low (latched unchanged)
}

void shift_byte( unsigned char b ) {
  char i;
  for ( i = 0; i < 8; i++ ) {
    if ( b & 0x01 ) {  // remember: invert the bits
      SET_PIN(C,4); // data high
    } else {
      CLR_PIN(C,4); // data low
    }
    CLR_PIN(C,5); // clock low
    b >>= 1; // next bit
    SET_PIN(C,5); // clock high (shift transition)
  }
}

void shift_digit( int8_t n ) {
  if ( n < 0 ) {
    shift_byte(0);
  } else {
    shift_byte( (digits[n]) << 1 );
  }
}

int main( void )
{
  init();
  while (1) {
    sleep_cpu();
  }
  return 0;
}

// right button: nop
ISR(PCINT0_vect)
{
}

// up/down/left buttons
ISR(PCINT2_vect)
{
  // Only left is a state change
  if ( !GET_PIN(D,7) ) { paused = !paused; }
}

// display modes
enum {
  MODE_HOURS,
  MODE_MINUTES,
  MODE_SECONDS,
  MODE_EXPIRED
};

volatile uint8_t flipper = 0;

ISR(TIMER1_COMPA_vect)
{
  char digits[DIGIT_COUNT];
  if (deciRemaining > 0 && !paused) {
    deciRemaining--;
  }
  flipper++;

  uint8_t mode = MODE_HOURS;
  if (deciRemaining < (60L*60L*10L)) { mode = MODE_MINUTES; }
  if (deciRemaining < (60L*10L)) { mode = MODE_SECONDS; }
  if (deciRemaining == 0) { mode = MODE_EXPIRED; }

  // Override display buttons
  if (!GET_PIN(B,0)) { // middle
    mode = MODE_HOURS;
  }
  if ( !GET_PIN(D,5) ) { // Up button
    mode = MODE_MINUTES;
  }
  if ( !GET_PIN(D,6) ) { // Down button
    mode = MODE_SECONDS;
  }

  int32_t displayValue;
  if (mode == MODE_HOURS) {
    displayValue = (deciRemaining / (60L*60L*10L));
  } else if (mode == MODE_MINUTES) {
    displayValue = (deciRemaining / (60L*10L)) % 60L;
  } else if (mode == MODE_SECONDS) {
    displayValue = (deciRemaining / 10L) % 60L;
  } else if (mode == MODE_EXPIRED) {
    displayValue = 8888;
  }
  
  int8_t idx;

  for (idx = 0; idx < 4; idx++) {
    int8_t digit;
    if (displayValue == 0) { 
      digit = -1;
    } else {
      digit = displayValue % 10L;
      displayValue /= 10L;
    }
    digits[idx] = digit;
  }
  if (digits[0] == -1) { digits[0] = 0; }
  
  // Flash digits if done or in partway mode
  if (paused || mode == MODE_EXPIRED) {
    if (flipper & 0x04) {
      for (int8_t i = 0; i < 4; i++) {
	digits[i] = -1;
      }
    }
  }

  start_shift();
  for (idx = DIGIT_COUNT; idx > 0; idx-- ) {
    shift_digit( digits[idx-1] );
  }
  end_shift();  
}
