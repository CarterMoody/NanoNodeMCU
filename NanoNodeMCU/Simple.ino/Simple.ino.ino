/*
 * Nano ESP8266 Trigger
 * Based on https://github.com/jamescoxon/Nano_Callback_System/blob/master/arduino_esp32/arduino_esp32.ino
 * Built up from the example code: WebSocketClient.ino
 *
 * Uses WebSockets Library https://github.com/Links2004/arduinoWebSockets which is LGPL, library remains untouched.
 *
 */

#include <Arduino.h>

#include <ESP8266WiFi.h>
#include <ESP8266WiFiMulti.h>
#include <ArduinoJson.h>
#include <WebSocketsClient.h>

ESP8266WiFiMulti WiFiMulti;
WebSocketsClient webSocket;

#define TRACKING_ADDRESS "xrb_3jwrszth46rk1mu7rmb4rhm54us8yg1gw3ipodftqtikf5yqdyr7471nsg1k"
#define WIFISSID "Moody"
#define WIFIPASS "freewalter"

#define LED_PIN 16

StaticJsonDocument<200> doc;
StaticJsonDocument<1024> rx_doc;

#define USE_SERIAL Serial

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {

  
  switch(type) {
    case WStype_DISCONNECTED:
      Serial.printf("[WSc] Disconnected!\n");
      break;
    case WStype_CONNECTED:
      Serial.printf("[WSc] Connected to url: %s\n", payload);

      // send message to server when Connected
      
      doc["address"] = TRACKING_ADDRESS;
      doc["api_key"] = "0";
      char output[512];
      serializeJson(doc, output);
      Serial.println(output);
      webSocket.sendTXT(output);
      break;
      
    case WStype_TEXT:
    {
      Serial.printf("[WSc] get text: %s\n", payload);
      deserializeJson(rx_doc, payload);
      String block_amount = rx_doc["amount"];
      
      long int noughtPointone = 100000;
      long int noughtPointtwo = 200000;
      Serial.println(block_amount);

      //Convert to nano
      int lastIndex = block_amount.length() - 24;
      block_amount.remove(lastIndex);

      Serial.println(block_amount);
      if (block_amount.toInt() > 100) {
        if (LED_PIN == 16) {
          digitalWrite(LED_PIN,LOW);
          delay(2000);
          digitalWrite(LED_PIN, HIGH); 
        }
      else{
          digitalWrite(LED_PIN,HIGH);
          delay(2000);
          digitalWrite(LED_PIN, LOW);
      }
      }
      // send message to server
      // webSocket.sendTXT("message here");
      break;
    }
    case WStype_BIN:
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

void setup() {
  pinMode(LED_PIN, OUTPUT);
  if (LED_PIN == 16) {
    digitalWrite(LED_PIN,LOW);
    delay(1000);
    digitalWrite(LED_PIN, HIGH); 
  }
  else{
    digitalWrite(LED_PIN,HIGH);
    delay(1000);
    digitalWrite(LED_PIN, LOW);
  }

  // USE_SERIAL.begin(921600);
  USE_SERIAL.begin(115200);

  //Serial.setDebugOutput(true);
  USE_SERIAL.setDebugOutput(true);

  USE_SERIAL.println();
  USE_SERIAL.println();
  USE_SERIAL.println();

  for(uint8_t t = 4; t > 0; t--) {
    USE_SERIAL.printf("[SETUP] BOOT WAIT %d...\n", t);
    USE_SERIAL.flush();
    delay(1000);
  }

  WiFiMulti.addAP(WIFISSID, WIFIPASS);
  

  //WiFi.disconnect();
  while(WiFiMulti.run() != WL_CONNECTED) {
    delay(100);
  }

  // server address, port and URL
  webSocket.begin("yapraiwallet.space", 80, "/call");

  // event handler
  webSocket.onEvent(webSocketEvent);

  // try ever 5000 again if connection has failed
  webSocket.setReconnectInterval(100);

}

void loop() {
  webSocket.loop();
}
