#include <avr/io.h>
#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <util/delay.h>
#include <stdio.h>
#include <string.h>
#include "mapping.hh"
#define F_CPU 16000000UL

void configureTimer() {
}

#define RX_BUF_SIZE 64
char rxBuf[RX_BUF_SIZE];
int rxOffset;
volatile bool has_command = false;

#define TX_BUF_SIZE 448
char txBuf[TX_BUF_SIZE];

char* pNextTx = NULL;

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
  pNextTx = pStr;
  UCSR0B |= (1 << UDRIE0);
}

/// Commands are of the form "[LTS][0-4]XX", where XX is the hex position
void processCommand()
{
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

#define IDLE_COUNT 500

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
    idle_count(0)
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
    PORTD = (PORTD & ~_BV(3)) | button?0:_BV(3);
}

bool getSpinButton() {
    // Spin button is active low
    return (PIND & _BV(2)) == 0;
}

int main( void )
{
  init();
  char* pMsg = "*** LUCKY CHERRY ***\n";
  char* pOk = "OK\n";
  char* pError = "?\n";
  uint8_t spin_trigger_cycles = 0;
  putString( pMsg );
  while (1) {
    bool spin_button = getSpinButton();
    if (!pass_trigger) spin_button = false;
    if (spin_trigger_cycles > 0) {
      spin_trigger_cycles--;
      spin_button = true;
    }
    setSpinButton(spin_button);

    if (has_command) {
      bool ok = false;
      if (rxBuf[0] == 'H') {
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
  if (pNextTx == 0 || *pNextTx == '\0') {
    UCSR0B &= ~(1 << UDRIE0);
  } else {
    UDR0=*pNextTx;
    pNextTx++;
  }
}

volatile bool is_running = false;

ISR(TIMER0_COMPA_vect)
{
  update();
  if (is_running) {
    is_running = !(left.isStopped() && 
		   center.isStopped() &&
		   right.isStopped());
    if (!is_running) {
      char buf[30];
      sprintf(buf,"SPIN %d %d %d\n",left.getCount(),
	      center.getCount(),
	      right.getCount());
      putString( buf );
    }
  } else {
    is_running = (!left.isStopped() ||
		  !center.isStopped() ||
		  !right.isStopped());
  }
}
