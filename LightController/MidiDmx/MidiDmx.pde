/* Midi In Basic  0.2 // kuki 8.2007
 *
 * -----------------
 * listen for midi serial data, and light leds for individual notes

 IMPORTANT:
 your arduino might not start if it receives data directly after a reset, because the bootloader thinks you want to uplad a new progam.
 you might need to unplug the midi-hardware until the board is running your program. that is when that statusLed turns on.

#####################################################################################################################################################
SOMETHING ABOUT MIDI MESSAGES
 midi messages start with one status byte followed by 1 _or_ 2 data bytes, depending on the command

 example midi message: 144-36-100
   the status byte "144" tells us what to do. "144" means "note on".
   in this case the second bytes tells us which note to play (36=middle C)
   the third byte is the velocity for that note (that is how powerful the note was struck= 100)
  
 example midi message: 128-36
   this message is a "note off" message (status byte = 128). it is followed by the note (data byte = 36)
   since "note off" messages don't need a velocity value (it's just OFF) there will be no third byte in this case
   NOTE: some midi keyboards will never send a "note off" message, but rather a "note on with zero velocity"
  
 do a web search for midi messages to learn more about aftertouch, poly-pressure, midi time code, midi clock and more interesting things.
#####################################################################################################################################################

HARDWARE NOTE:
The Midi Socket is connected to arduino RX through an opto-isolator to invert the midi dmxPinnal and seperate the circuits of individual instruments.
connect 8 leds to pin2-pin9 on your arduino.

####################################################################################################################################################


 */

#include "pins_arduino.h"
#include <EEPROM.h>

#define SWITCH_CONTROL true
#define FADER_CONTROL false
#define NUM_CHANNELS 8

byte incomingByte;

int dmxPin = 9;
int switchPin = 2;

boolean receivedCommand = false;

int param=0;
int params[2];
char dmx[NUM_CHANNELS];

char dmxFull = 255;
char dmxOff = 0;

boolean switchState = LOW;
boolean reading = LOW;

void setup() {
  pinMode(dmxPin, OUTPUT);
  pinMode(switchPin, INPUT);

  Serial.begin(31250);
  
  for (int x = 0; x < NUM_CHANNELS; x++) {
    dmx[x] = EEPROM.read(x); 
  }
  
}

void loop () {
  
  reading = digitalRead(switchPin);
  if (reading != switchState) {
    int switchedValue;
    if (reading == HIGH)     switchedValue = dmxFull;
    else if (reading == LOW) switchedValue = dmxOff;
    for (int x=0; x<NUM_CHANNELS; x++) {
      dmx[x] = switchedValue;
    }
    saveState();
    switchState = reading; 
  }
  
  if (Serial.available() > 0) {
    // read the incoming byte:
    incomingByte = Serial.read();
    
    if (receivedCommand) {
      params[param] = incomingByte;
      param++;
      
      if (param == 2) {
        param = 0;
        receivedCommand = false;
        
        char chan = params[0];
        char brightness = map(params[1], 0, 127, 20, 255);
        dmx[chan] = brightness;
        saveState();
      }
    }
    
    // wait for as status-byte, channel 1, continuous controller message
    if (incomingByte== 0xB0) receivedCommand = true;
  }
  
  // sending the break (the break can be between 88us and 1sec)
  digitalWrite(dmxPin, LOW);

  delay(10);

  // sending the start byte
  shiftDmxOut(dmxPin, 0);
  
  for (int x = 0; x < 10; x++)
  {
    shiftDmxOut(dmxPin, dmx[x]);
  }
}

void saveState() {
  
  for (int x = 0; x < NUM_CHANNELS; x++) {
    EEPROM.write(x, dmx[x]); 
  }
 
}

/* Sends a DMX byte out on a pin.  Assumes a 16 MHz clock.
* Disables interrupts, which will disrupt the millis() function if used
* too frequently. */
void shiftDmxOut(int pin, int theByte)
{
int port_to_output[] = {
NOT_A_PORT,
NOT_A_PORT,
_SFR_IO_ADDR(PORTB),
_SFR_IO_ADDR(PORTC),
_SFR_IO_ADDR(PORTD)
};

int portNumber = port_to_output[digitalPinToPort(pin)];
int pinMask = digitalPinToBitMask(pin);

// the first thing we do is to write te pin to high
// it will be the mark between bytes. It may be also
// high from before
_SFR_BYTE(_SFR_IO8(portNumber)) |= pinMask;
delayMicroseconds(10);

// disable interrupts, otherwise the timer 0 overflow interrupt that
// tracks milliseconds will make us delay longer than we want.
cli();

// DMX starts with a start-bit that must always be zero
_SFR_BYTE(_SFR_IO8(portNumber)) &= ~pinMask;

// we need a delay of 4us (then one bit is transfered)
// this seems more stable then using delayMicroseconds
asm("nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n");
asm("nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n");

asm("nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n");
asm("nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n");

asm("nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n");
asm("nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n");

for (int i = 0; i < 8; i++)
{
if (theByte & 01)
{
_SFR_BYTE(_SFR_IO8(portNumber)) |= pinMask;
}
else
{
_SFR_BYTE(_SFR_IO8(portNumber)) &= ~pinMask;
}

asm("nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n");
asm("nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n");

asm("nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n");
asm("nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n");

asm("nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n");
asm("nop\n nop\n nop\n nop\n nop\n nop\n nop\n nop\n");

theByte >>= 1;
}

// the last thing we do is to write the pin to high
// it will be the mark between bytes. (this break is have to be between 8 us and 1 sec)
_SFR_BYTE(_SFR_IO8(portNumber)) |= pinMask;

// reenable interrupts.
sei();
}

