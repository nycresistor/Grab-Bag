#include <stdint.h>
#include <avr/io.h>
#include <avr/interrupt.h>

#define MODULES 6
#define ROWS 7
#define COLUMNS (60*MODULES)

#define BYTES_PER_ROW ((COLUMNS+7)/8)

uint8_t bit_buffer[ROWS*BYTES_PER_ROW];

volatile uint8_t *buf_wr_ptr;
volatile uint8_t wr_bytes;

volatile uint8_t current_line;

void init_spi() {
  DDRB |= _BV(5) | _BV(3) | _BV(2);
  SPCR = _BV(SPIE) | _BV(SPE) | _BV(MSTR) | 
    _BV(CPOL) | _BV(CPHA) | _BV(SPR0);
  SPSR = _BV(SPI2X);
}

#define TIMER2_TICKS_PER_ROW 145

void init_vblank_timer() {
  OCR2A = TIMER2_TICKS_PER_ROW;
  TCCR2A = _BV(WGM21);
  TCCR2B = _BV(CS22) | _BV(CS21);
  TIMSK2 = _BV(OCIE2A);
}

void write_line() {
  // assert no line
  buf_wr_ptr = bit_buffer + (BYTES_PER_ROW * current_line);
  wr_bytes = BYTES_PER_ROW - 1;
  SPDR = *buf_wr_ptr;
  buf_wr_ptr++;
}

int main() {
  cli();
  current_line = 0;
  init_spi();
  init_vblank_timer();
  sei();
  while (1) {
    // check for frame flag
    // update
    // sleep
  }
}

ISR(TIMER2_COMPA_vect) {
  current_line++;
  if (current_line >= ROWS) { current_line = 0; }
  write_line();
}

ISR(SPI_STC_vect) {
  if (wr_bytes > 0) {
    SPDR = *buf_wr_ptr;
    buf_wr_ptr++;
    wr_bytes--;
  } else {
    // assert current_line
  }
}
