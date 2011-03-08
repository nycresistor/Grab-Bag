#include <stdint.h>
#include <avr/io.h>
#include <avr/interrupt.h>

#define THERMISTOR_PIN 3

void init_thermistor() {
  DDRC &= ~(_BV(THERMISTOR_PIN));
  PORTC &= ~(_BV(THERMISTOR_PIN));
  ADCSRA |= _BV(ADPS2) | _BV(ADPS1) | _BV(ADPS0) |
    _BV(ADEN);
}

#define ANALOG_REF 3

int16_t do_thermistor_read() {
  ADMUX = (ANALOG_REF << 6) | (THERMISTOR_PIN & 0x0f);
  // start the conversion.
  ADCSRA |= _BV(ADSC);
  while ((ADCSRA & _BV(ADSC)) != 0);
  uint8_t low_byte = ADCL;
  uint8_t high_byte = ADCH;
  return (high_byte << 8) | low_byte;
}

// MEGA168_DOUBLE_SPEED_MODE is 1 if USXn is 1.
#ifndef MEGA168_DOUBLE_SPEED_MODE
#define MEGA168_DOUBLE_SPEED_MODE 0
#endif

#if MEGA168_DOUBLE_SPEED_MODE
#define UBRR_VALUE 51
#define UCSR0A_VALUE _BV(U2X0)
#else
#define UBRR_VALUE 25
#define UCSR0A_VALUE 0
#endif

void init_serial() {
  UBRR0H = UBRR_VALUE >> 8;
  UBRR0L = UBRR_VALUE & 0xff;
  /* set config for uart, explicitly clear TX interrupt flag */
  UCSR0A = UCSR0A_VALUE | _BV(TXC0);
  UCSR0B = _BV(RXEN0) | _BV(TXEN0);
  UCSR0C = _BV(UCSZ01)|_BV(UCSZ00);
  /* defaults to 8-bit, no parity, 1 stop bit */
}

void print_serial(char* pTxt) {
  while(*pTxt != '\0') {
    UCSR0A |= _BV(TXC0);
    UDR0 = *pTxt;
    while ((UCSR0A & _BV(TXC0)) == 0);
    pTxt++;
  }
}
  
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
  init_thermistor();
  sei();
  set_solenoid(true);
  while (1) {
    print_serial("fdasfdsa\n");
    uint16_t temp = do_thermistor_read();
  }
}
