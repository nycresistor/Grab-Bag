#define F_CPU 16000000UL
#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <util/delay.h>
#include <stdio.h>
#include <string.h>
#include "mapping.hh"

void configureTimer() {
}

#define RX_BUF_SIZE 64
char rxBuf[RX_BUF_SIZE];
int rxOffset;
volatile bool has_command = false;

#define TX_BUF_SIZE 448
char txBuf[TX_BUF_SIZE];

volatile char* pStartTx = txBuf;
volatile char* pEndTx = txBuf;

// True if spin lever should be enabled; false
// otherwise.
volatile bool pass_trigger = true;

void configureSerial() {
  // Setting to 9600 baud, 8N1, @ 16Mhz
  // 9600 baud: U2X = 1, UBRR = 207
  UBRR0H = 0;
  UBRR0L = 207;
  UCSR0A = 0x02;
  // enable TX/RX
  UCSR0B = (1<<RXCIE0) | (1<<RXEN0) | (1<<TXEN0);
  // 8 bits, no parity, 1 stop bit
  UCSR0C = (1<<UCSZ01) | (1<<UCSZ00);
  rxOffset = 0;
}

void putString( char* pStr ) {
  do {
    *(pEndTx++) = *(pStr++);
    if (pEndTx >= (txBuf + TX_BUF_SIZE)) {
      pEndTx = txBuf;
    }
  } while (*pStr != '\0');
  UCSR0B |= (1 << UDRIE0);
}

bool getCS1() {
    //  button is active low
    return (PIND & _BV(5)) == 0;
}

bool getCS2() {
    //  button is active low
    return (PIND & _BV(6)) == 0;
}

void setCS1(bool value) {
  //  button is active low
  const uint8_t bit = _BV(7);
  PORTD = (PORTD & (~bit)) | (value?0:bit);
}

void setCS2(bool value) {
  //  button is active low
  PORTB = (PORTB & ~_BV(0)) | value?0:_BV(0);
}

void configurePins()
{
  // Port C is input
  DDRC = 0x00;
  // Port D: 2, 5, 6 are input
  //         3, 4, 7 are output
  DDRD |= _BV(3) | _BV(4) | _BV(7);
  // Port B: 0 is output
  DDRB |= _BV(0);
  setCS1(false);
  setCS2(false);

}

#define OCR_VALUE 32
#define UPDATE_TICKS (16*2000)/OCR_VALUE
void configureTimers()
{
  TCCR0A = 0x02;
  TCCR0B = 0x04;
  OCR0A = OCR_VALUE;
  TIMSK0 = _BV(OCIE0A);
}

#define PINLS 4
#define PINCS 2
#define PINRS 0

#define PINLO 5
#define PINCO 3
#define PINRO 1

#define SAMPLES 4
// Debounced signals
class Signal {
private:
  volatile uint8_t run;
  volatile bool state;
  volatile bool changed;
public:
  Signal(bool start = true) : run(0),
			      state(start),
			      changed(false)
  {}

  void update(const bool latest) {
    changed = false;
    if (latest == state) { run = 0; }
    else {
      run++;
      if (run >= SAMPLES) {
	run = 0;
	changed = true;
	state = latest;
      }
    }
  }

  bool hasRise() { return state && changed; }
  bool hasFall() { return (!state) && changed; }
  bool getState() { return state; }
  bool getChanged() { return changed; }
};

#define IDLE_COUNT 300
#define INITIAL_COUNT 1600

class Wheel {
private:
  const uint8_t stepper_pin;
  const uint8_t opto_pin;
  Signal stepper;
  Signal opto;
  volatile bool opto_triggered_flag;
  volatile uint8_t count;
  volatile uint16_t idle_count;
public:
  Wheel(const uint8_t stepper_pin_in,
	const uint8_t opto_pin_in) :
    stepper_pin(stepper_pin_in),
    opto_pin(opto_pin_in),
    stepper(true),
    opto(true),
    opto_triggered_flag(false),
    count(0),
    idle_count(IDLE_COUNT)
  {}

  const uint8_t getCount() const { 
    return table[count%50];
  }
  
  void update(const uint8_t pins) {
    const bool stepper_value = (_BV(stepper_pin) & pins) != 0;
    const bool opto_value = (_BV(opto_pin) & pins) != 0;
    stepper.update(stepper_value);
    opto.update(opto_value);

    // on falling opto, set opto flag and *skip rest of update*
    if (opto.hasFall()) { opto_triggered_flag = true; return; }

    // on falling stepper, increment count
    if (stepper.hasFall()) {
      count++;
      if (opto_triggered_flag) {
	count = 0;
	opto_triggered_flag = false;
      }
      idle_count = 0;
    } else {
      idle_count++;
      if (idle_count > IDLE_COUNT) {
	idle_count = IDLE_COUNT;
      }
    }
  }

  const bool isStopped() {
    return idle_count >= IDLE_COUNT;
  }
};

Wheel left(PINLS,PINLO);
Wheel center(PINCS,PINCO);
Wheel right(PINRS,PINRO);

void update() {
  const uint8_t pins = PINC;
  left.update(pins);
  center.update(pins);
  right.update(pins);
}

void init()
{
  cli();
  configurePins();
  configureSerial();
  configureTimers();
  sei();
}


#define SPIN_BUTTON    0
#define MAX_BET_BUTTON 1
#define COIN_1_BUTTON  2
#define COIN_2_BUTTON  3

void setSpinButton(bool button) {
    // Spin button is active low
  const uint8_t bit = _BV(3);
  PORTD = (PORTD & (~bit)) | (button?0:bit);
}

bool getSpinButton() {
    // Spin button is active low
    return (PIND & _BV(2)) == 0;
}


enum {
  CS_WAIT,
  CS_TRIGGER_1,
  CS_TRIGGER_BOTH,
  CS_TRIGGER_2
};

int main( void )
{
  init();
  char* pMsg = "*** LUCKY CHERRY ***\n";
  char* pOk = "OK\n";
  char* pError = "?\n";
  uint8_t spin_trigger_cycles = 0;
  uint8_t cs_trigger_state = CS_WAIT;
  uint8_t cs_output_state = CS_WAIT;
  int8_t cs_output_waits = 0;
  putString( pMsg );
  while (1) {
    bool spin_button = getSpinButton();
    if (!pass_trigger) spin_button = false;
    if (spin_trigger_cycles > 0) {
      spin_trigger_cycles--;
      spin_button = true;
    }
    setSpinButton(spin_button);

    // Check coinslot
    switch (cs_trigger_state) {
    case CS_WAIT:
      if (getCS1()) {
	cs_trigger_state = CS_TRIGGER_1;
      }
      break;
    case CS_TRIGGER_1:
      if (!getCS1()) {
	cs_trigger_state = CS_WAIT;
      } else if (getCS2()) {
	cs_trigger_state = CS_TRIGGER_BOTH;
      }
      break;
    case CS_TRIGGER_BOTH:
      if (!getCS2()) {
	cs_trigger_state = CS_WAIT;
      } else if (!getCS1()) {
	cs_trigger_state = CS_TRIGGER_2;
      }
      break;
    case CS_TRIGGER_2:
      if (!getCS2()) {
	cs_trigger_state = CS_WAIT;
	putString("COIN\n");
      } 
    }

    switch (cs_output_state) {
    case CS_WAIT:
      break;
    case CS_TRIGGER_1:
      cs_output_waits--;
      if (cs_output_waits <= 0) {
	cs_output_state = CS_TRIGGER_BOTH;
	cs_output_waits = 12;
	setCS2(true);
      }
      break;
    case CS_TRIGGER_BOTH:
      cs_output_waits--;
      if (cs_output_waits <= 0) {
	cs_output_state = CS_TRIGGER_2;
	cs_output_waits = 3;
	setCS1(false);
      }
      break;
    case CS_TRIGGER_2:
      cs_output_waits--;
      if (cs_output_waits <= 0) {
	cs_output_state = CS_WAIT;
	cs_output_waits = 0;
	setCS2(false);
      }
      break;
    }

    if (has_command) {
      bool ok = false;
      if (rxBuf[0] == 'H') {
	ok = true;
      } else if (rxBuf[0] == 'C') {
	cs_output_state = CS_TRIGGER_1;
	cs_output_waits = 5;
	setCS1(true);
	ok = true;
      } else if (rxBuf[0] == 'L') {
	// lever operation
	if (rxBuf[1] == 'p') {
	  pass_trigger = true;
	  ok = true;
	} else if (rxBuf[1] == 'b') {
	  pass_trigger = false;
	  ok = true;
	} else if (rxBuf[1] == 't') {
	  spin_trigger_cycles = 100;
	  ok = true;
	}
      }
      putString( ok?pOk:pError );
      has_command = false;
    }
    _delay_ms(1);
  }
  return 0;
}

ISR(USART_RX_vect)
{  
  rxBuf[ rxOffset ] = UDR0;
  if ( rxBuf[ rxOffset ] == '\n' ) {
    rxBuf[ rxOffset ] = '\0';
    rxOffset = 0;
    has_command = true;
  } else {
    rxOffset = (rxOffset+1) % RX_BUF_SIZE;
  }
}

ISR(USART_UDRE_vect)
{
  if (pEndTx == pStartTx) {
    UCSR0B &= ~(1 << UDRIE0);
  } else {
    UDR0=*pStartTx;
    pStartTx++;
    if (pStartTx >= (txBuf + TX_BUF_SIZE)) {
      pStartTx = txBuf;
    }
  }
}

volatile bool is_running = false;
volatile bool left_running = false;
volatile bool center_running = false;
volatile bool right_running = false;
volatile uint16_t initial_delay = 0;

ISR(TIMER0_COMPA_vect)
{
  update();
  if (is_running) {
    if (initial_delay < INITIAL_COUNT) { initial_delay++; }
    else {
      char buf[30];
      if (left.isStopped() && left_running) {
	left_running = false;
	sprintf(buf,"WHEEL L %d\n",left.getCount());
	putString(buf);
      }
      if (center.isStopped() && center_running) {
	center_running = false;
	sprintf(buf,"WHEEL C %d\n",center.getCount());
	putString(buf);
      }
      if (right.isStopped() && right_running) {
	right_running = false;
	sprintf(buf,"WHEEL R %d\n",right.getCount());
	putString(buf);
      }
      is_running = !(left.isStopped() && 
		     center.isStopped() &&
		     right.isStopped());
      if (!is_running) {
	sprintf(buf,"SPIN RESULT %d %d %d\n",left.getCount(),
		center.getCount(),
		right.getCount());
	putString( buf );
      }
    }
  } else {
    is_running = (!left.isStopped() ||
		  !center.isStopped() ||
		  !right.isStopped());
    if (is_running) {
      initial_delay = 0;
      left_running = right_running = center_running = true;
      putString((char*)"START SPIN\n");
    }
  }
}
