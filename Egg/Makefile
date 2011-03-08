UISP = avrdude -c usbtiny -P usb -p m168 -F

COMPILE = avr-g++ -Wall -Os -Iusbdrv -I. -mmcu=atmega168 #-DDEBUG_LEVEL=1

OBJECTS = egg.o

# symbolic targets:
all:	egg.hex

.c.o:
	$(COMPILE) -c $< -o $@

.cc.o:
	$(COMPILE) -c $< -o $@

.S.o:
	$(COMPILE) -x assembler-with-cpp -c $< -o $@

.c.s:
	$(COMPILE) -S $< -o $@

flash:	all
	$(UISP) -U flash:w:main.hex -v

# Set to 12MHz external clock, low power
# High: 1101 1111 0xdf
#  Low: 0110 1111 0x6f    SUT 10 CKSEL 1111 CDIV 0 (div/8 on)
fuses168:
	$(UISP) -U lfuse:w:0x6f:m
	$(UISP) -U hfuse:w:0xdf:m 


clean:
	rm -f egg.bin egg.hex egg.eep.hex $(OBJECTS)

# file targets:
egg.bin:	$(OBJECTS)
	$(COMPILE) -o egg.bin $(OBJECTS)

egg.hex:	egg.bin
	rm -f egg.hex egg.eep.hex
	avr-objcopy -j .text -j .data -O ihex egg.bin egg.hex

# do the checksize script as our last action to allow successful compilation
# on Windows with WinAVR where the Unix commands will fail.
