#include <CPE123_Fall16.h>

// Just tests a motor, no other hardware needed

// PINOUTS
// RX0<-0 = Green pin from Xbee Second Pin from left
// TX0->1 = Blue pin from Xbee 3rd Pin from left (middle pin)
// 5V = Purple to Xbee Last pin far right
// GND = Gray to Xbee 4th pin from left
// 13 = White to motor
// 12 = Yellow to motor
// 9 = Blue to Motor
// 8 = Green to Motor
// 7 = Gray to IN3 (3rd pin) on Motor Controller unit
// 6 = Yellow to IN4 (4th pin) on Motor Controller unit
// Red and Black Power linked from Wall Block to Motor Controller to Board


const int motor1A = 6;
const int motor1B = 7;

unsigned long real60M = 1000UL * 60 * 60;
int delay30S = 1000 * 30;
unsigned long adjusted60M = (real60M - delay30S) - 4000;
//int delay5S = 1000 * 5;

// Code from CircuitDigest to Read from Serial XBEE Communication
int received = 0;
int i;
/////


// Delay Timers
unsigned long DELAY_TIME_MIN = 60; // Edit this to specific time between feedings NOTICE NOT A DOUBLE
unsigned long ONE_SECOND = 1000; // 1.0 seconds in milliseconds
unsigned long DELAY_TIME_MILLI = ONE_SECOND * 60.0 * DELAY_TIME_MIN;
unsigned long delayStart = 0; // The time the delay started
bool delayRunning = false; // True if still waiting for delay to finish


bool runIndependently = false; // Set to True to run regular feedings on Arduino NOT RPi

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  
  Serial.print("Begin: ");
  Serial.println(__FILE__);

   // Initalize the pins for output 
   pinMode(motor1A, OUTPUT);
   pinMode(motor1B, OUTPUT);

    // Stop the motor
   analogWrite(motor1A, 0);
   analogWrite(motor1B, 0);

   Serial.println("Staring motor testing");

   pinMode(LED_BUILTIN, OUTPUT);

   blinkInternal();

   // start delay timer
   delayStart = millis();
   
   delayRunning = true;
   Serial.print("DELAY_TIME_MILLI: ");
   Serial.println(DELAY_TIME_MILLI);
   
   
   feedBirds();
   
  }

// Runs motors for 2 seconds (2000ms)
void feedBirds(){
  analogWrite(motor1A, 0);
  analogWrite(motor1B, 250);
  
  delay(800);
 
  analogWrite(motor1A, 0);
  analogWrite(motor1B, 0);

}

// Does nothing but blink builtin LED 3 times, once every .5 seconds
void blinkInternal(){
  digitalWrite(LED_BUILTIN, HIGH);
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
  delay(500);

  digitalWrite(LED_BUILTIN, HIGH);
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
  delay(500);

  digitalWrite(LED_BUILTIN, HIGH);
  delay(500);
  digitalWrite(LED_BUILTIN, LOW);
  delay(500);

}

void loop() {
  // put your main code here, to run repeatedly:

  Serial.print("runIndependently: ");
  Serial.println(runIndependently);
  if (runIndependently) // True if not relying on RPi for signal to feed (set bool above)
  {
      Serial.println("in running Independently");
      // Check if delay has timed out
      unsigned long timeSinceLastDelay = millis() - delayStart;
      Serial.print("timeSinceLastDelay: ");
      Serial.println(timeSinceLastDelay);
      if (delayRunning && (timeSinceLastDelay >= DELAY_TIME_MILLI))
      {
        Serial.println("delay time reached");
        delayStart += DELAY_TIME_MILLI; // This prevents drift in the delays
        feedBirds(); // do delayed action
      }
        
  }
  
  if (Serial.available() > 0) 
  {
    //blinkInternal();

    received = Serial.read();
    Serial.print(received);
    if (received == 'a'){
      feedBirds();
    }
  }
  
}
