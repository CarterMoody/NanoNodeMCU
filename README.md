# NanoNodeMCU
React to NANO Network on NodeMCU

Youtube Demonstration: https://www.youtube.com/watch?v=CvavXIPLnDg

Most of the credit must be given to this writeup: https://medium.com/the-nano-center/nano-esp8266-trigger-build-guide-f17f7a6517b2

Description of Folders/Files: (all of these monitor NTP server)

1. NanoMqtt: Monitors Nano Network and mqtt server (RPI).

2. NanoNodeMCU: Monitors Nano Network on the Arduino device

3. NodeMCUmqtt: Monitors MQTT Server as Client

4. RPi: Contains files to be run on RPi

5.  YoutubeMQTT.py : Hosts MQTT Server and Monitors YouTube Live Chat

6.  YoutubeMqttNano.py : Most updated file for the RPi, listens on Websocket for Nano Transactions, Monitors YT Live Chat, and communicates with Arduino NodeMCU via MQTT


# Instructions: https://docs.google.com/document/d/11qHZTV_VtY0-6eIIvyDKzXHq9InnWSXJNmRCBqyEh5M/edit?usp=sharing
