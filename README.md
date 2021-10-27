# NanoNodeMCU
React to NANO Network on NodeMCU

Youtube Demonstration: https://www.youtube.com/watch?v=CvavXIPLnDg

Most of the credit must be given to this writeup: https://medium.com/the-nano-center/nano-esp8266-trigger-build-guide-f17f7a6517b2

MQTT Simple Explanation for this program    
Client - Arduino program.ino    
Broker - RPI Background Process (Mosquitto server)    
Client2 - RPI program.py    
Clients subscribe to certain 'topics', and publish to 'topics'. The broker sees all messages published.    

Description of Folders/Files: (all of these monitor NTP server)    

DahuaAPI\    
  pdf - Shows API specific to my Dahua Live cam.    
  SSH and Curl - API examples    
  set48.sh - Sets Audio sampling frequency to 48000    
  set64.sh - Sets Audio sampling frequency to 64000    

MqttMotor\    
  MqttMotor.ino 
    - Connects to MQTT broker (RPI)    
    - sends heartbeats    
    - responds to MQTT messages    
    - spins motor    

RPi\    
  MqttServerPahoWorking.py 
    - Simple implementation of MQTT client in Python for testing.    
  YoutubeMqttNano.py     
    - Fully fledged program    
    - Connects to MQTT broker (RPI)    
    - listens for hearbeats from NodeMCU Arduino and responds with heartbeat Acknowledgement (ACK)    
    - sends MQTT messages    
    - Monitors NANO network via websocket    
    - Monitors Youtube Live chat via google API    
  forever    
    - simple bash program to cause infinite running of python program    
    - Needs work/research. shell=true is not safe.     
    - Requires python modules installed at sudo system-wide level.    
    - Should be switched to use pyenv    
    - Requires changing default OS python version to new python3 install    
  nodes.json    
    - list of nodes for Nano Websocket functionality    
  requirements.txt    
    - list of requirements for Nano Websocket functionality    
   
Testing\    
  mqttPahoSubClientWorking.ino    
    - very simple working Arduino code for MQTT client    

# Instructions: https://docs.google.com/document/d/11qHZTV_VtY0-6eIIvyDKzXHq9InnWSXJNmRCBqyEh5M/edit?usp=sharing
