// Blinks the built-in LED

#include "wirish.h"
#include "usb.h"
#include "timer.h"
#define X_ENCODER_A 5 //PB6 Timer4_CH1
#define X_ENCODER_B 9 //PB7 Timer4_CH2
#define Y_ENCODER_A 6 //PA8 Timer1_CH1
#define Y_ENCODER_B 7 //PB9 Timer1_CH2

unsigned short knob_val=0;
unsigned short pwm_x=0;
unsigned short pwm_y=0;
signed long current_x=0;
signed long current_y=0;
signed short delta_x=0,delta_y=0;


void setup() {
    pinMode(14, OUTPUT);
    pinMode(24, OUTPUT);
    pinMode(29, OUTPUT);
    pinMode(3, INPUT_ANALOG);
    pinMode(X_ENCODER_A, INPUT);
    pinMode(X_ENCODER_B, INPUT);
    pinMode(Y_ENCODER_A, INPUT);
    pinMode(Y_ENCODER_B, INPUT);
    pinMode(11,PWM);    
    digitalWrite(24,1);
    SerialUSB.println("Hello");
    timer_init(TIMER1);
    timer_init(TIMER4);
    timer_pause(TIMER1);
    timer_pause(TIMER4);
    timer_set_prescaler(TIMER1,0);
    timer_set_prescaler(TIMER4,0);
    (TIMER4->regs).gen->CCMR1 |= TIMER_CCMR1_CC2S;  //enable input2
    (TIMER4->regs).gen->CCMR1 |= TIMER_CCMR1_CC1S;  //enable input1
    (TIMER4->regs).gen->CCMR1 |= 0x3<<12; // IC2F Filter
    (TIMER4->regs).gen->CCMR1 |= 0x3<<4;  // IC1F Filter
    (TIMER4->regs).gen->CCER &= ~(TIMER_CCER_CC1P); //non-inverted polarity channel 1
    (TIMER4->regs).gen->CCER &= ~(TIMER_CCER_CC2P); //non-inverted polarity channel 2
    (TIMER4->regs).gen->SMCR |= TIMER_SMCR_SMS_ENCODER3;
    (TIMER1->regs).gen->CCMR1 |= TIMER_CCMR1_CC2S;
    (TIMER1->regs).gen->CCMR1 |= TIMER_CCMR1_CC1S;
    (TIMER1->regs).gen->CCMR1 |= 0x3<<12; // IC2F Filter
    (TIMER1->regs).gen->CCMR1 |= 0x3<<4;  // IC1F Filter
    (TIMER1->regs).gen->CCER &= ~(TIMER_CCER_CC1P);
    (TIMER1->regs).gen->CCER &= ~(TIMER_CCER_CC2P);
    (TIMER1->regs).gen->SMCR |= TIMER_SMCR_SMS_ENCODER3;
    timer_generate_update(TIMER1);
    timer_generate_update(TIMER4);
    timer_resume(TIMER1);
    timer_resume(TIMER4);    
}

int toggle = 1;
int toggle2 = 0;
void loop() {
    // You could just use toggleLED() instead, but this illustrates
    // the use of digitalWrite():
    knob_val=analogRead(3);
    pwm_x=32768+(knob_val<<2)-8192;
    delta_x=(signed short)timer_get_count(TIMER4);
    delta_y=(signed short)timer_get_count(TIMER1);
    current_x+=delta_x;
    current_y+=delta_y;
    timer_set_count(TIMER4,timer_get_count(TIMER4)-delta_x);
    timer_set_count(TIMER1,timer_get_count(TIMER1)-delta_y);
    pwmWrite(11,pwm_x);
    SerialUSB.print("Output:");
    SerialUSB.print(pwm_x);
    SerialUSB.print(" X_pos:");
    SerialUSB.println(current_x);
    digitalWrite(14, toggle);
    digitalWrite(24, toggle2);
    digitalWrite(29, toggle);
    toggle ^= 1;
    toggle2 ^= 1;
    //delay(10);
}

// Force init to be called *first*, i.e. before static object allocation.
// Otherwise, statically allocated objects that need libmaple may fail.
__attribute__((constructor)) void premain() {
    init();
}

int main(void) {
    setup();

    while (true) {
        loop();
    }
    return 0;
}
