/*
  Nathan Seidle
  SparkFun Electronics 2011
  
  This code is public domain but you buy me a beer if you use this and we meet someday (Beerware license).
  
  Controlling an LED strip with individually controllable RGB LEDs. This stuff is awesome.
  
  The SparkFun (individually controllable) RGB strip contains a bunch of WS2801 ICs. These
  are controlled over a simple data and clock setup. The WS2801 is really cool! Each IC has its
  own internal clock so that it can do all the PWM for that specific LED for you. Each IC
  requires 24 bits of 'greyscale' data. This means you can have 256 levels of red, 256 of blue,
  and 256 levels of green for each RGB LED. REALLY granular.
 
  To control the strip, you clock in data continually. Each IC automatically passes the data onto
  the next IC. Once you pause for more than 500us, each IC 'posts' or begins to output the color data
  you just clocked in. So, clock in (24bits * 32LEDs = ) 768 bits, then pause for 500us. Then
  repeat if you wish to display something new.
  
  This example code will display bright red, green, and blue, then 'trickle' random colors down 
  the LED strip.
  
  You will need to connect 5V/Gnd from the Arduino (USB power seems to be sufficient).
  
  For the data pins, please pay attention to the arrow printed on the strip. You will need to connect to
  the end that is the begining of the arrows (data connection)--->
  
  If you have a 4-pin connection:
  Blue = 5V
  Red = SDI
  Green = CKI
  Black = GND
  
  If you have a split 5-pin connection:
  2-pin Red+Black = 5V/GND
  Green = CKI
  Red = SDI
 */
#include <EEPROM.h>


int SDI = 12; //Red wire (not the red 5V wire!)
int CKI = 13; //Green wire


#define STRIP_LENGTH 32 //32 LEDs on this strip
long strip_colors[STRIP_LENGTH];

long orange = 0xFF3000;
long pink = 0xFF0030;
long red = 0xFF0000;
long blue = 0x0000FF;
long white = 0xFFFFFF;

int mode = 0;

void setup() {
  pinMode(SDI, OUTPUT);
  pinMode(CKI, OUTPUT);

  
  //Clear out the array
  for(int x = 0 ; x < STRIP_LENGTH ; x++)
    strip_colors[x] = 0;
  
  Serial.begin(9600);
  Serial.println("Hello!");

  
  int modifier = EEPROM.read(0);
  if (modifier == 255 || modifier == 4) modifier = 0;
  
  Serial.print("Mod: ");
  Serial.println(modifier);
  
  if (modifier) {
  for (int x=0; x < modifier; x++) {
    orange = (orange >> 1) & 0x7f7f7f;
    pink = (pink >> 1) & 0x7f7f7f;
    white = (white >> 1) & 0x7f7f7f;
    blue = (blue >> 1) & 0x7f7f7f;
    red = (red >>1 ) & 0x7f7f7f;
    white = (white >> 1) & 0x7f7f7f;
    blue = (blue >> 1) & 0x7f7f7f;
    red = (red >>1 ) & 0x7f7f7f;
  }
  
  }
  
  Serial.print("Orange: ");
  Serial.println(orange, HEX);
  Serial.print("Pink: ");
  Serial.println(pink, HEX);
  Serial.print("White: ");
  Serial.println(white, HEX);
  
  EEPROM.write(0, modifier + 1);
}

void loop() {
  //Pre-fill the color array with known values

  post_frame(); //Push the current color frame to the strip
  
  delay(500);

  while(1){ //Do nothing
    

    
    switch (mode) {
     
     case 0: stream();
     case 1: blink();
     case 2: swirl();
     case 3: checker();
     case 4: whitestrobe();
     case 5: popo();
     case 6: cylon();
     case 7: blinkstream();
     case 8: crazystrobe();
     case 9: mode = 0; 
      
      
    }

    
  }
}

void crazystrobe(void) {
  
  long color;
  
 for (int y=0; y < 50; y++) {
  
   if (y % 4 == 0) color = orange;
   else if (y % 4 ==1 || y % 4 == 3) color = white;
   else color = pink;
    
   setAll(color);
   post_frame();
   
   delay(30);
   
   clearFrame();
   post_frame();
   delay(150);
   
  
 } 
  
  
}


void setAll(long color) {
  for (int x=0; x < STRIP_LENGTH; x++) {
       strip_colors[x] = color;
  } 
  
}

void cylon(void) {
  
  int pos = 0;

  boolean forward = true;
  
 for (int y=0; y < 10; y++) {

   for (int x=0; x < STRIP_LENGTH; x++) {
     clearFrame();
     post_frame();
     delay(10);
     
     long color = forward? pink: orange;
     
     strip_colors[pos] = color;
     strip_colors[pos +1] = color;
     strip_colors[pos +2] = color;
     strip_colors[pos +3] = color;
     
     if (forward) pos++;
     else pos--;
     
     post_frame();
     
     if (pos == STRIP_LENGTH - 3 || (pos == 0 && forward == false)) forward = !forward;
     
     delay(40);
      
   }
 }
 
 mode++;
 
}

void whitestrobe(void) {
  
 for (int y=0; y < 20; y++) {

 
   setAll(white);
   post_frame();
   
   delay(5);
   
   clearFrame();
   post_frame();
   
   delay(random(100,500));
   
 }
  
  mode++;
  
}

void popo(void) {
  
  for (int y=0; y < 10; y++) {

    long color = (y % 2 ==0)? red : blue;
     
     setAll(color);
     
     delay(200);
     post_frame();
    
  }
  
  mode++;
  
}


void checker(void) {
 
 for (int y=0; y < 50; y++) {
  
   long color1, color2;
   
  if (y % 2 == 0) {
    color1 = pink;
    color2 = orange;
  } else {
     color1 = orange;
    color2 = pink; 
  }
   
  for (int x=0; x < STRIP_LENGTH; x++) {
     if (x % 2 ==0) strip_colors[x] = color1;
     else strip_colors[x] = color2;
  }
 
   post_frame();

   
   delay(200);
   
   
 }
  
  mode++;
}

void swirl(void) {
 
  
  for (int y=0; y < 10; y++) {
    

    
   // long color = (y % 2 ==0)? pink: orange;
  
    if (y % 2 ==0) {
      strip_colors[0] = pink;
    } else {
      strip_colors[0] = orange; 
    }
    
    
    post_frame();
    
    for (int q=0; q < STRIP_LENGTH; q++) {
      

        for(int x = (STRIP_LENGTH - 1) ; x > 0 ; x--) strip_colors[x] = strip_colors[x - 1];
  
        post_frame();
        delay(25);
      }
  }
    mode++;
}

void blink(void) {
 
  
 for (int y=0; y < 20; y++ ) { 
   
   long color = (y % 2 == 0)? orange : pink;
   
   setAll(color);
   
   post_frame();
   delay(20);
   
   clearFrame();
   post_frame();
   delay(300);
   
 }
 
 mode++;
}

void clearFrame(void) {
      for (int x=0; x < STRIP_LENGTH; x++) {
      strip_colors[x] = 0x000000;
   }
   //post_frame();
}

//Throws random colors down the strip array
void stream(void) {
  
  for (int y = 0; y < 100; y++) {
  
    int x;
    
    //First, shuffle all the current colors down one spot on the strip
    for(x = (STRIP_LENGTH - 1) ; x > 0 ; x--)
      strip_colors[x] = strip_colors[x - 1];

  
    long color = random(0,2)? orange : pink;
    
    delay(50);
  
    strip_colors[0] = color; //Add the new random color to the strip
    strip_colors[1] = color;
    
    post_frame();
    
    delay(50);
    
  }
}

void blinkstream(void) {
  
  for (int y = 0; y < 100; y++) {
  
    int x;
    
    //First, shuffle all the current colors down one spot on the strip
    for(x = (STRIP_LENGTH - 1) ; x > 0 ; x--)
      strip_colors[x] = strip_colors[x - 1];

  
    long color = random(0,2)? orange : pink;
    
    delay(50);
  
    strip_colors[0] = color; //Add the new random color to the strip
    strip_colors[1] = color;
    
    post_frame();
    
    long stripCopy[STRIP_LENGTH];
    for (int q=0; q < STRIP_LENGTH; q++) {
      stripCopy[q] = strip_colors[q]; 
    }
    
    delay(30);
    clearFrame();
    post_frame();
    delay(50);
    
    for (int q=0; q < STRIP_LENGTH; q++) {
      strip_colors[q] = stripCopy[q]; 
    }
    
  }
}


//Takes the current strip color array and pushes it out
void post_frame (void) {
  //Each LED requires 24 bits of data
  //MSB: R7, R6, R5..., G7, G6..., B7, B6... B0 
  //Once the 24 bits have been delivered, the IC immediately relays these bits to its neighbor
  //Pulling the clock low for 500us or more causes the IC to post the data.

  for(int LED_number = 0 ; LED_number < STRIP_LENGTH ; LED_number++) {
    long this_led_color = strip_colors[LED_number]; //24 bits of color data

    for(byte color_bit = 23 ; color_bit != 255 ; color_bit--) {
      //Feed color bit 23 first (red data MSB)
      
      digitalWrite(CKI, LOW); //Only change data when clock is low
      
      long mask = 1L << color_bit;
      //The 1'L' forces the 1 to start as a 32 bit number, otherwise it defaults to 16-bit.
      
      if(this_led_color & mask) 
        digitalWrite(SDI, HIGH);
      else
        digitalWrite(SDI, LOW);
  
      digitalWrite(CKI, HIGH); //Data is latched when clock goes high
    }
  }

  //Pull clock low to put strip into reset/post mode
  digitalWrite(CKI, LOW);
  delayMicroseconds(500); //Wait for 500us to go into reset
}
