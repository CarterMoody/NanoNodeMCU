/*************************************************** 
  NodeMCU
****************************************************/

// MqttMotor.ino
//
// This code connects to an MQTT broker as a client and monitors
//    for messages. If it gets one to run the motor, it will do so.
//    It will also send a heartbeat back to the Broker so that
//    it is clear it is still connected.
//    In addition, it connects to an NTP server
//    to monitor time change.

// NodeMCU 1.0 ESP-12E Pinout image here:
//    https://www.instructables.com/NodeMCU-ESP8266-Details-and-Pinout/
//    Note that D2 is a PWM
//    Note that D0 and D4 correspond to the onboard LED's on the NodeMCU and ESP-12, respectively.

// NodeMCU Onboard LED explanation here:
//    https://lowvoltage.github.io/2017/07/09/Onboard-LEDs-NodeMCU-Got-Two

// L298N Pinout image here:
//    https://lastminuteengineers.com/l298n-dc-stepper-driver-arduino-tutorial/

// NODEMCU PINOUTS
// D2 = Purple to resistor on breadboard before LED
// D1 = Gray to IN1 (1st pin) on Motor Controller unit
// D7 = Yellow to IN2 (2nd pin) on Motor Controller unit // This has some output on boot, but less than D3
// GND = Black to breadboard Ground rail connected to both LED and L928N Ground
// VIN = Red to +5V on L298N (this powers the NodeMCU, there is a regulator on NodeMCU from VIN that steps it down to 3.3v)

// L298N PINOUTS
//    Both jumpers are still installed in default place from factory, on (ENA)(+5V) and (ENB)(+5V)
// OUT1 = Red to Motor Red
// OUT2 = Black to Motor Black
// +12V aka VCC = Red to Positive (+) DC Female Barrel Plug
// GND = Black to Negative (-) DC Female Barrel Plug
// +5V = Red to VIN NodeMCU (powers NodeMCU)
// IN1 = Gray to D3 on NodeMCU   ****NEEDS UPDATED****
// IN2 = Yellow to D4 on NodeMCU ****NEEDS UPDATED****

// MOTOR PINOUT 12V DC Motor 6Pin with Encoder
// Red Positive (+) = L298N OUT1
// Black Negative (-) = L298N OUT2
// Green Hall Sensor GND = UNUSED
// Blue Hall Sensor Vcc = UNUSED
// Yellow Hall Sensor A Vout = UNUSED
// White Hall Sensor B Vout = UNUSED
////////////

#include <Arduino.h>
#include <NTPClient.h>            // https://github.com/arduino-libraries/NTPClient
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <WiFiUdp.h>
#include <PubSubClient.h>         // https://github.com/knolleary/pubsubclient
#include <ArduinoJson.h>          // https://github.com/bblanchon/ArduinoJson
#include <WebSocketsClient.h>     // https://github.com/Links2004/arduinoWebSockets/tree/master/src
#include "Adafruit_MQTT.h"        // https://github.com/adafruit/Adafruit_MQTT_Library
#include "Adafruit_MQTT_Client.h"
#include <string.h>
/************************* WiFi Access Point and MQTT Globals *********************************/ 
#define WLAN_SSID         "Moody" 
#define WLAN_PASS         "PASSWORD" 
#define mqtt_server       IPAddress (192, 168, 1, 213) // static ip address of the Raspberry Pi MQTT Server
#define MQTT_PORT         1883                    
#define MQTT_USERNAME     ""    // Not necessarily needed
#define MQTT_PASSWORD     ""    // Not necessarily needed
/************************* Pins and other HW setup Globals  *********************************/ 
#define LED_PIN           D1    // Pin connected to the LED
#define NodeMCU_LED       16
#define ESP12_LED         2
#define motor1A_PIN       D1
#define motor1B_PIN       D7
#define USE_SERIAL        Serial
/************************* Wifi and MQTT continued setup *********************************/  
// Create an ESP8266 WiFiClient class to connect to the MQTT server. 
WiFiClient espClient;
// Setup the MQTT client class by passing in the WiFi client
PubSubClient client(espClient);
unsigned long lastMsg = 0;
#define MSG_BUFFER_SIZE  (50)
char msg[MSG_BUFFER_SIZE];
int value = 0;
/************************* Timing Globals *********************************/ 
int lastFeedHour = 0;                           // Global keeps track of last hour feed was dispensed
int lastHeartbeatHour = 0;                      // Global keeps track of last time heartbeat was sent
int lastHeartbeatMinute = 0;                      // Global keeps track of last minute heartbeat was sent
int global_mqtt_retries = 3;                    // Global keeps track of how many time we will try the mqtt_check() procedure.
int MOTOR_RUN_TIME = 1000;                      // Global sets for how long motor is to turn in milliseconds
/*************************** NTP Stuff **************************************/
const long utcOffstHours = -7; // Set this to your offset from UTC time. PST is UTC-8 for example so put -8
const long utcOffsetInSeconds = 60 * 60 * utcOffstHours; // Calculated based off your offset specified in utcOffsetHours
int FEEDING_HOURS[] = {7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21}; // Set these to the hours you want to feed
int FEEDING_HOURS_SIZE = sizeof FEEDING_HOURS / sizeof FEEDING_HOURS[0];
char daysOfTheWeek[7][12] = {"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"};
// Define NTP Client to get time
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", utcOffsetInSeconds);
/*************************** Function Headers *******************************/
void bootMessage();
void stopMotors();
void runMotorClockWise(int run_time);
void runMotorCounterClockWise(int run_time);
void blinkUniversal(int led_type, int times, int delay_time);
void blinkInternal(int led_type, int times, int delay_time);
void fadeLED();
void checkHourlyFeed();
void heartbeatCheck();
void sendHeartbeat();
void printTime();
void printTimeStamp();
void MQTT_connect();
void Mqtt_check();
void setup_wifi();
String buildStringFromBytesObject(byte* bytesArray, unsigned int length);

/*************************** Sketch Code ************************************/ 
void setup() { 
    Serial.begin(115200);
    USE_SERIAL.setDebugOutput(true);
    bootMessage();
    // Initalize the pins for output
    pinMode(motor1A_PIN, OUTPUT);
    pinMode(motor1B_PIN, OUTPUT);
    pinMode(LED_PIN, OUTPUT);
    pinMode(NodeMCU_LED, OUTPUT); // Internal LED on NodeMCU
    pinMode(ESP12_LED, OUTPUT);   // Internal LED on ESP-12
    digitalWrite(NodeMCU_LED, HIGH); // Turn off LED
    digitalWrite(ESP12_LED, HIGH);   // Turn off LED

    setup_wifi();

    client.setServer(mqtt_server, 1883);
    client.setCallback(callback); // What to do when we receive a message on a channel we subscribe to

    // Stop the motor
    stopMotors();

    timeClient.begin();
    timeClient.update();
    printTime();

    blinkInternal(NodeMCU_LED, 3, 500); // blink 3 times, once every .5 seconds, to show we started successfully.
    runMotorClockWise(MOTOR_RUN_TIME);  // Test motor on startup
    printTimeStamp();
    Serial.println("Setup Complete");
}

uint32_t x=0;

void loop() {
    timeClient.update();
    //checkHourlyFeed();
    heartbeatCheck();

    // MQTT stuff
    if (!client.connected()) {
      reconnect();
    }
    client.loop();
}

void setup_wifi() {

  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(WLAN_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WLAN_SSID, WLAN_PASS);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  randomSeed(micros());

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}


// This method turns a byteArray into a string for printing, or comparison, or anything really.
String buildStringFromBytesObject(byte* bytesArray, unsigned int length){
  String constructedString = "";
  for (int i = 0; i < length; i++) {
    constructedString += (char)bytesArray[i];
  }
  return constructedString;
}

// This function is called when a message is received on a MQTT topic that we subscribe to
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [ ");
  Serial.print(topic);
  Serial.println(" ]");
  
  String decoded_payload_string = buildStringFromBytesObject(payload, length); // payload is originally a bytes object
  Serial.print("decoded_payload_string: ");
  Serial.println(decoded_payload_string);
  if ( strcmp(topic, "nodemcu/heartbeatAcknowledged") == 0 )
  {
    Serial.println("topic is: nodemcu/heartbeatAcknowledged");
    if (decoded_payload_string == "heartbeatAcknowledged"){
      Serial.println("our heartbeat was acknowledged");
    }
  }
  if ( strcmp(topic, "nodemcu/runmotor") == 0 )
  {
      Serial.println("running motor!");
      runMotorClockWise(MOTOR_RUN_TIME);
  }
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);
    // Attempt to connect
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      // Once connected, publish an announcement...
      client.publish("outTopic", "hello world");
      // ... and resubscribe
      client.subscribe("#");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}


// Print a message and delay a bit on boot
void bootMessage(){
    for (uint8_t t = 4; t > 0; t--)
    {
        printTimeStamp();
        USE_SERIAL.printf("[SETUP] BOOT WAIT %d...\n", t);
        USE_SERIAL.flush();
        delay(1000);
    }
}

// Stops the motors
//    both pins low or both pins high will stop motors
void stopMotors()
{
    digitalWrite(motor1A_PIN, LOW);
    digitalWrite(motor1B_PIN, LOW);

    digitalWrite(LED_PIN, LOW);
}

// Run motors for given time. Swap which pin is high/low to change direction of spin
void runMotorClockWise(int run_time)
{
    digitalWrite(LED_PIN, HIGH);

    digitalWrite(motor1A_PIN, LOW);
    digitalWrite(motor1B_PIN, HIGH);

    delay(run_time);
    stopMotors();
}

// Run motors for given time. Swap which pin is high/low to change direction of spin
void runMotorCounterClockWise(int run_time)
{
    digitalWrite(LED_PIN, HIGH);

    digitalWrite(motor1A_PIN, HIGH);
    digitalWrite(motor1B_PIN, LOW);

    delay(run_time);
    stopMotors();
}

// Pass in which LED to blink, number of times to blink, and rate of blink
//  delay_time is in milliseconds where 500 = .5 seconds
void blinkUniversal(int led_type, int times, int delay_time)
{
    for (int i = 1; i <= times; i++)
    {
        digitalWrite(led_type, HIGH);
        delay(delay_time);
        digitalWrite(led_type, LOW);
        if (i != times)
        {
            delay(delay_time);
        }
    }
}

// Pass in which LED to blink, number of times to blink, and rate of blink
//  delay_time is in milliseconds where 500 = .5 seconds
void blinkInternal(int led_type, int times, int delay_time)
{
    // Built in LED's on NodeMCU operate in "inverted" in regard to pin levels
    for (int i = 1; i <= times; i++)
    {
        digitalWrite(led_type, LOW);
        delay(delay_time);
        digitalWrite(led_type, HIGH);
        if (i != times)
        {
            delay(delay_time);
        }
    }
}

// Function that fades LED via a PWM pin on the board.
//  Check pinout to find out other available PWM pins
void fadeLED()
{
    for (int brightness = 1; brightness <= 255; brightness++)
    {
        analogWrite(LED_PIN, brightness);
        delay(10);
    }
    for (int brightness = 255; brightness > 0; brightness--)
    {
        analogWrite(LED_PIN, brightness);
        delay(10);
    }
}


// updates lastFeedHour to currentHour
void updateHourlyFeed()
{
    int currentHour = timeClient.getHours();
    lastFeedHour = currentHour; 
}

// updates lastHeartbeatHour to currentHour
void updateHeartbeat()
{
    int currentMinute = timeClient.getMinutes();
    lastHeartbeatMinute = currentMinute;    
}

bool isFeedHour(int currentHour)
{
    for (int i = 0; i < FEEDING_HOURS_SIZE; i++)
    {
        if (currentHour == FEEDING_HOURS[i])
        {
            return true;
        }
    }
    return false;
}

// Compare current Hour to lastFeedHour, if different then send heartbeat
void heartbeatCheck()
{
    int currentMinute = timeClient.getMinutes();
    if (currentMinute != lastHeartbeatMinute)
    {
        printTimeStamp();
        Serial.println("Have not sent heartbeat this minute");
        sendHeartbeat();
        updateHeartbeat();
    }
}

// send heartbeat to RPI
void sendHeartbeat()
{
    char mqtt_message[MSG_BUFFER_SIZE];
    snprintf(mqtt_message, MSG_BUFFER_SIZE, "heartbeat");
    //Serial.print("mqtt_message: ");
    //Serial.println(mqtt_message);
    client.publish("nodemcu/heartbeat", mqtt_message); 
}

// Compare current Hour to lastFeedHour, if different then feed
void checkHourlyFeed()
{
    int currentHour = timeClient.getHours();
    if ( isFeedHour(currentHour) )
    {
        if (currentHour != lastFeedHour)
        {
            printTimeStamp();
            Serial.println("Have not fed this hour");
            runMotorClockWise(MOTOR_RUN_TIME);
            updateHourlyFeed();
        }
    }
}

void printTime()
{
    Serial.print(daysOfTheWeek[timeClient.getDay()]);
    Serial.print(", ");
    Serial.print(timeClient.getHours());
    Serial.print(":");
    Serial.print(timeClient.getMinutes());
    Serial.print(":");
    Serial.println(timeClient.getSeconds());
    //Serial.println(timeClient.getFormattedTime());
}

void printTimeStamp()
{
    Serial.print("[");
    Serial.print(timeClient.getFormattedTime());
    Serial.print("] ");
}
