#define encoder0PinA 2
#define encoder0PinB 3
#define OUTPUT_PIN 9
#include<stdint.h>
#include <PID_v1.h>

volatile int64_t encoder0Pos = 0;
int64_t oldPos,velocity;
uint32_t lasttime, currenttime;

int16_t commanded_v;
int16_t commanded_a;

//Define Variables we'll be connecting to
double Setpoint_p, Input_p, Output_p;
double Setpoint_v, Input_v, Output_v;

//Define the aggressive and conservative Tuning Parameters
double consKp_p=.2, consKi_p=0.05, consKd_p=0.1;
double consKp_v=.6, consKi_v=0.00, consKd_v=0.0;

int16_t max_a=15;
int16_t max_v=2048;

PID myPID_p(&Input_p, &Output_p, &Setpoint_p, consKp_p, consKi_p, consKd_p, DIRECT);
PID myPID_v(&Input_v, &Output_v, &Setpoint_v, consKp_v, consKi_v, consKd_v, DIRECT);

void setup() {
  pinMode(encoder0PinA, INPUT); 
  pinMode(encoder0PinB, INPUT); 
  pinMode(OUTPUT_PIN,OUTPUT);
// encoder pin on interrupt 0 (pin 2)
  attachInterrupt(0, doEncoderA, CHANGE);
// encoder pin on interrupt 1 (pin 3)
  attachInterrupt(1, doEncoderB, CHANGE);  
  Serial.begin (119200);
  Setpoint_p = 10000;
  Setpoint_v = 0;
  oldPos=0;
  velocity=0;
  currenttime=lasttime=millis();
  //turn the PID on
  myPID_p.SetMode(AUTOMATIC);
  myPID_v.SetMode(AUTOMATIC);
}
void loop(){ //Do stuff here 
  Input_p = encoder0Pos;
  currenttime=millis();
  if((currenttime-lasttime)>10){
    velocity=Input_p-oldPos;
    Input_v=(Input_v*.8)+(velocity*.2);
    oldPos=Input_p;
    lasttime=currenttime;
    myPID_v.Compute();
  }
  double gap = abs(Setpoint_p-Input_p); //distance away from setpoint
  double v_diff = abs(Setpoint_v-Input_v);
  
  myPID_p.Compute();
  
  commanded_v=(Output_p/255.0)*(max_v*2)-max_v;
  Setpoint_v=commanded_v;
  
  
  commanded_a=(Output_v/255.0)*(max_a*2)-max_a;
  
  Serial.print("Accel Out:");
  Serial.print(commanded_a);
  Serial.print(" Velocity Command:");
  Serial.print(commanded_v);
  Serial.print(" Velocity:");
  Serial.print(Input_v);
  Serial.print(" Position:");
  Serial.println((int32_t)encoder0Pos);
  analogWrite(OUTPUT_PIN,128-(commanded_a));
  if (Serial.available()){
    char C = Serial.read();
    if (C == '-'){
       Setpoint_p=Setpoint_p - 1000;
    }else if (C == '+'){
      Setpoint_p=Setpoint_p + 1000;
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

