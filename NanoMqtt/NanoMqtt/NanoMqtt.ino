/*************************************************** 
  NodeMCU
****************************************************/

// NanoMqtt.ino
//
// This code monitors a nano address for an incoming transaction and
//    if the amount is greater than minimum_threshold_Mnano then
//    the motor turns for a given amount of time. LED will also light
//    up during this time. In addition to this, the code will connect
//    to a running mqtt server on the raspberrypi and listen for
//    additional commands. In addition, it connects to an NTP server
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
// GND = Black to breadboard Ground rail connected to LED
// GND = Black to GND on L298N
// VIN = Red to +5V on L298N (this powers the NodeMCU, there is a regulator on NodeMCU from VIN that steps it down to 3.3v)

// L298N PINOUTS
//    Both jumpers are still installed in default place from factory, on (ENA)(+5V) and (ENB)(+5V)
// OUT1 = Red to Motor Red
// OUT2 = Black to Motor Black
// +12V aka VCC = Red to Positive (+) DC Female Barrel Plug
// GND = Black to Negative (-) DC Female Barrel Plug
// +5V = Red to VIN NodeMCU (powers NodeMCU)
// IN1 = Gray to D3 on NodeMCU
// IN2 = Yellow to D4 on NodeMCU

// MOTOR PINOUT 12V DC Motor 6Pin with Encoder
// Red Positive (+) = L298N OUT1
// Black Negative (-) = L298N OUT2
// Green Hall Sensor GND = UNUSED
// Blue Hall Sensor Vcc = UNUSED
// Yellow Hall Sensor A Vout = UNUSED
// White Hall Sensor B Vout = UNUSED
////////////

#include <Arduino.h>
#include <NTPClient.h> // https://github.com/arduino-libraries/NTPClient
#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h> // https://github.com/bblanchon/ArduinoJson
#include <WebSocketsClient.h> // https://github.com/Links2004/arduinoWebSockets/tree/master/src
#include "Adafruit_MQTT.h" 
#include "Adafruit_MQTT_Client.h" 
/************************* WiFi Access Point *********************************/ 
#define WLAN_SSID       "" 
#define WLAN_PASS        "" 
#define MQTT_SERVER      "192.168.1.118" // static ip address
#define MQTT_PORT         1883                    
#define MQTT_USERNAME    "" 
#define MQTT_PASSWORD         ""
#define TRACKING_ADDRESS "nano_1ae75uxbfmpdqreejgziwut1ufj7e9othf1efo1byfocsjuoe63rtdmo1fg4"
#define LED_PIN     D1                // Pin connected to the LED
#define NodeMCU_LED 16
#define ESP12_LED 2
#define motor1A_PIN D1
#define motor1B_PIN D7
#define USE_SERIAL Serial
/************ Globals ***********************/
const float minimum_threshold_Mnano = 0; // Global to be set to minimum required Mnano NANO donation before reacting
int lastFeedHour = 0; // Global keeps track of last hour feed was dispensed
/************ Global State ******************/ 
// Create an ESP8266 WiFiClient class to connect to the MQTT server. 
WiFiClient client;
WebSocketsClient webSocket;
// Setup the MQTT client class by passing in the WiFi client and MQTT server and login details. 
Adafruit_MQTT_Client mqtt(&client, MQTT_SERVER, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD); 
/****************************** Feeds ***************************************/ 
// Setup a feed called 'pi_led' for publishing. 
// Notice MQTT paths for AIO follow the form: <username>/feeds/<feedname> 
Adafruit_MQTT_Publish pi_led = Adafruit_MQTT_Publish(&mqtt, MQTT_USERNAME "/leds/pi"); 
// Setup a feed called 'esp8266_led' for subscribing to changes. 
Adafruit_MQTT_Subscribe esp8266_led = Adafruit_MQTT_Subscribe(&mqtt, MQTT_USERNAME "/leds/esp8266");
/*************************** ArduinoJson Stuff ******************************/
StaticJsonDocument<200> doc;
StaticJsonDocument<1024> rx_doc;
/*************************** NTP Stuff **************************************/
const long utcOffsetInSeconds = 3600;
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
void webSocketEvent(WStype_t type, uint8_t *payload, size_t length);
void checkHourlyFeed();
void printTime();
void printTimeStamp();
void MQTT_connect();
void Mqtt_check();


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

 Serial.print("Connecting to "); 
 Serial.println(WLAN_SSID); 
 WiFi.begin(WLAN_SSID, WLAN_PASS); 
 while (WiFi.status() != WL_CONNECTED) { 
   delay(500); 
   Serial.print("."); 
 } 
 Serial.println(); 
 Serial.println("WiFi connected"); 
 Serial.println("IP address: "); Serial.println(WiFi.localIP()); 

 //WiFiMulti.addAP(WIFISSID, WIFIPASS);

 //WiFi.disconnect();
 //while (WiFiMulti.run() != WL_CONNECTED)
 //{
   //delay(100);
 //}

 // server address, port and URL
 webSocket.begin("yapraiwallet.space", 80, "/call");

 // event handler
 webSocket.onEvent(webSocketEvent);

 // try ever 5000 again if connection has failed
 webSocket.setReconnectInterval(5000);
 // Setup MQTT subscription for esp8266_led feed. 
 mqtt.subscribe(&esp8266_led);

 // Stop the motor
 stopMotors();

 timeClient.begin();
 timeClient.update();
 printTime();

 blinkInternal(NodeMCU_LED, 3, 500);
 printTimeStamp();
 Serial.println("Setup Complete");
}

uint32_t x=0;

void loop() {
  timeClient.update();
  checkHourlyFeed();
  mqtt_check();
  webSocket.loop();
}




void mqtt_check(){
 // Ensure the connection to the MQTT server is alive (this will make the first 
 // connection and automatically reconnect when disconnected).  See the MQTT_connect 
 MQTT_connect(); 
 // this is our 'wait for incoming subscription packets' busy subloop 
 // try to spend your time here 
 // Here its read the subscription 
 Adafruit_MQTT_Subscribe *subscription; 
 while ((subscription = mqtt.readSubscription())) { 
   if (subscription == &esp8266_led) { 
     char *message = (char *)esp8266_led.lastread; 
     Serial.print(F("Got: ")); 
     Serial.println(message); 
        // Check if the message was ON, OFF, TOGGLE, or RUNMOTOR 
     if (strncmp(message, "ON", 2) == 0) { 
       // Turn the LED on. 
       digitalWrite(LED_PIN, HIGH); 
     } 
     else if (strncmp(message, "OFF", 3) == 0) { 
       // Turn the LED off. 
       digitalWrite(LED_PIN, LOW); 
     } 
     else if (strncmp(message, "TOGGLE", 6) == 0) { 
       // Toggle the LED. 
       digitalWrite(LED_PIN, !digitalRead(LED_PIN)); 
     }
     else if (strncmp(message, "RUNMOTOR", 8) == 0) {
       // Run those motors
       runMotorClockWise(1000);
     }
   } 
 } 
 //delay(20); // not sure if needed
}

// Function to connect and reconnect as necessary to the MQTT server. 
void MQTT_connect() { 
 int8_t ret; 
 // Stop if already connected. 
 if (mqtt.connected()) { 
   return; 
 } 
 Serial.print("Connecting to MQTT... "); 
 uint8_t retries = 3; 
 while ((ret = mqtt.connect()) != 0) { // connect will return 0 for connected 
      Serial.println(mqtt.connectErrorString(ret)); 
      Serial.println("Retrying MQTT connection in 5 seconds..."); 
      mqtt.disconnect(); 
      delay(5000);  // wait 5 seconds 
      retries--; 
      if (retries == 0) { 
        // basically die and wait for WDT to reset me 
        while (1); 
      } 
 } 
 Serial.println("MQTT Connected!"); 
}

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

void webSocketEvent(WStype_t type, uint8_t *payload, size_t length)
{

    switch (type)
    {
    case WStype_DISCONNECTED:
        printTimeStamp();
        Serial.printf("[WSc] Disconnected!\n");
        break;
    case WStype_CONNECTED:
        printTimeStamp();
        Serial.printf("[WSc] Connected to url: %s\n", payload);

        // send message to server when Connected

        doc["address"] = TRACKING_ADDRESS;
        doc["api_key"] = "0";
        char output[512];
        serializeJson(doc, output);
        printTimeStamp();
        Serial.println(output);
        webSocket.sendTXT(output);

        //fadeLED(); // to signify connected
        blinkInternal(ESP12_LED, 2, 500); // to signify connected
        //blinkNodeMCU(3, 500);
        break;

    case WStype_TEXT:
    {
        printTimeStamp();
        Serial.printf("[WSc] get text: %s\n", payload);
        deserializeJson(rx_doc, payload);
        String block_amount_raw = rx_doc["amount"];

        // Convert to nano
        int nanoIndex = block_amount_raw.length() - 24;
        String block_amount_nano_string = block_amount_raw;
        block_amount_nano_string.remove(nanoIndex);
        int block_amount_nano = block_amount_nano_string.toInt();

        double block_amount_Mnano = block_amount_nano / (pow(10, 6));

        printTimeStamp();
        Serial.print("Amount in raw: ");
        Serial.println(block_amount_raw);
        printTimeStamp();
        Serial.print("Amount in NANO/Nano/Mnano: ");
        Serial.println(block_amount_Mnano);

        // Check if Donation amount > minimumThreshold
        if (block_amount_raw.toInt() > minimum_threshold_Mnano)
        {
            runMotorClockWise(1000);
        }
    }
    break;

    case WStype_BIN:
        printTimeStamp();
        Serial.printf("[WSc] get binary length: %u\n", length);
        hexdump(payload, length);

        // send data to server
        // webSocket.sendBIN(payload, length);
        break;
    case WStype_ERROR:
    case WStype_FRAGMENT_TEXT_START:
    case WStype_FRAGMENT_BIN_START:
    case WStype_FRAGMENT:
    case WStype_FRAGMENT_FIN:
        break;
    }
}

// Compare current Hour to lastFeedHour, if different then feed
void checkHourlyFeed()
{
    int currentHour = timeClient.getHours();
    if (currentHour != lastFeedHour)
    {
        printTimeStamp();
        Serial.println("Have not fed this hour");
        runMotorClockWise(1000);
        lastFeedHour = currentHour;
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
