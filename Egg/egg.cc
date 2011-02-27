#include <stdint.h>
#include <avr/io.h>
#include <avr/interrupt.h>

void set_solenoid(bool on) {
  if (on) {
    PORTD |= _BV(2);
  } else {
    PORTD &= ~_BV(2);
  }
}

// solenoid on d2
void init_solenoid() {
  set_solenoid(false);
  DDRD |= _BV(2);
}

int main() {
  cli();
  init_solenoid();
  sei();
  set_solenoid(true);
  while (1) {
  }
}
