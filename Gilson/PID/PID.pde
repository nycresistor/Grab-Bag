#define encoder0PinA 2
#define encoder0PinB 3
#define OUTPUT_PIN 9
#include<stdint.h>
#include <PID_v1.h>

volatile int32_t encoder0Pos = 0;
uint16_t control;

//Define Variables we'll be connecting to
double Setpoint, Input, Output;

//Define the aggressive and conservative Tuning Parameters
double aggKp=.5, aggKi=0.2, aggKd=1;
double consKp=.1, consKi=0.04, consKd=0.03;
double range=20.0;
PID myPID(&Input, &Output, &Setpoint, consKp, consKi, consKd, DIRECT);

void setup() {
  pinMode(encoder0PinA, INPUT); 
  pinMode(encoder0PinB, INPUT); 
  pinMode(OUTPUT_PIN,OUTPUT);
// encoder pin on interrupt 0 (pin 2)
  attachInterrupt(0, doEncoderA, CHANGE);
// encoder pin on interrupt 1 (pin 3)
  attachInterrupt(1, doEncoderB, CHANGE);  
  Serial.begin (119200);
  Setpoint = 10000;
  //turn the PID on
  myPID.SetMode(AUTOMATIC);
}
void loop(){ //Do stuff here 
  Input = encoder0Pos;
  
  double gap = abs(Setpoint-Input); //distance away from setpoint
  
  if(1)
  {  //we're close to setpoint, use conservative tuning parameters
    myPID.SetTunings(consKp, consKi, consKd);
  }
  else
  {
     //we're far from setpoint, use aggressive tuning parameters
     myPID.SetTunings(aggKp, aggKi, aggKd);
  }
  
  myPID.Compute();
  control=128+5+range;
  control=control-(Output/255.0*(range*2));

  Serial.print(Output);
  Serial.print(" ");
  Serial.print(control);
  Serial.print(" ");
  Serial.println(encoder0Pos);
  analogWrite(OUTPUT_PIN,control);
  if (Serial.available()){
    char C = Serial.read();
    if (C == '-'){
       Setpoint=Setpoint - 1000;
    }else if (C == '+'){
      Setpoint=Setpoint + 1000;
    }      
  }
}

void doEncoderA(){
  // look for a low-to-high on channel A
  if (digitalRead(encoder0PinA) == HIGH) { 
    // check channel B to see which way encoder is turning
    if (digitalRead(encoder0PinB) == LOW) {  
      encoder0Pos = encoder0Pos - 1;         // CW
    } 
    else {
      encoder0Pos = encoder0Pos + 1;         // CCW
    }
  }
  else   // must be a high-to-low edge on channel A                                       
  { 
    // check channel B to see which way encoder is turning  
    if (digitalRead(encoder0PinB) == HIGH) {   
      encoder0Pos = encoder0Pos - 1;          // CW
    } 
    else {
      encoder0Pos = encoder0Pos + 1;          // CCW
    }
  }

}
void doEncoderB(){
  // look for a low-to-high on channel B
  if (digitalRead(encoder0PinB) == HIGH) {   
   // check channel A to see which way encoder is turning
    if (digitalRead(encoder0PinA) == HIGH) {  
      encoder0Pos = encoder0Pos - 1;         // CW
    } 
    else {
      encoder0Pos = encoder0Pos + 1;         // CCW
    }
  }
  // Look for a high-to-low on channel B
  else { 
    // check channel B to see which way encoder is turning  
    if (digitalRead(encoder0PinA) == LOW) {   
      encoder0Pos = encoder0Pos - 1;          // CW
    } 
    else {
      encoder0Pos = encoder0Pos + 1;          // CCW
    }
  }
}
