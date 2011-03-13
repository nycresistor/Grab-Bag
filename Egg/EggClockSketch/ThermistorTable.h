#ifndef THERMISTOR_TABLE
#define THERMISTOR_TABLE

#include <stdint.h>

#define NUMTEMPS 20

int16_t thermistorToCelsius(int16_t reading);

#endif // THERMISTOR_TABLE
