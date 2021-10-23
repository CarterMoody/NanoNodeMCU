# RPi
import time 
#import RPi.GPIO as GPIO 
import paho.mqtt.client as mqtt

# Configuration:

# Setup callback functions that are called when MQTT events happen like 
# connecting to the server or receiving data from a subscribed feed. 
def on_connect(client, userdata, flags, rc): 
    print("Connected with result code " + str(rc)) 
    # Subscribing in on_connect() means that if we lose the connection and 
    # reconnect then subscriptions will be renewed. 
    client.subscribe("#") 
# The callback for when a PUBLISH message is received from the server. 
def on_message(client, userdata, msg): 
    print(msg.topic+" "+str( msg.payload)) 
    # Check if this is a message for the Pi LED. 
    if msg.topic == 'outTopic': 
         # Look at the message data and perform the appropriate action. 
        if msg.payload == "hello world": 
            print("hi!")
           
           
# Show status of sensors  
    #room1
    if msg.topic == "/birdFeeder/status":
        if msg.payload == "1":
            print ("Topic: ", msg.topic + "\nMessage: " + str(msg.payload))
    if msg.topic == "/birdFeeder//status":
        if msg.payload == "0":
            print ("Topic: ", msg.topic + "\nMessage: " + str(msg.payload))


# Create MQTT client and connect to localhost, i.e. the Raspberry Pi running 
# this script and the MQTT server.
mqtt_broker_ip = "localhost"
client = mqtt.Client() 
client.on_connect = on_connect 
client.on_message = on_message 
client.connect(mqtt_broker_ip, 1883, 60) 
# Connect to the MQTT server and process messages in a background thread. (Non-blocking)
#client.looop_start()
client.loop_forever()
# Main loop to listen for button presses. 
print('Script is running, press Ctrl-C to quit...') 
time.sleep(3)
while True: 
   # Look for a change from high to low value on the button input to 
   # signal a button press. 
   ##button_first = GPIO.input(BUTTON_PIN) 
   ##time.sleep(0.02)  # Delay for about 20 milliseconds to debounce. 
   ##button_second = GPIO.input(BUTTON_PIN) 
   ##if button_first == GPIO.HIGH and button_second == GPIO.LOW: 
       ##print('Button pressed!') 
       ## Send a toggle message to the ESP8266 LED topic. 
       ##client.publish('/leds/esp8266', 'TOGGLE')
   print('Sending message to esp8266')
   #client.publish('/leds/esp8266', 'TOGGLE')
   time.sleep(1)