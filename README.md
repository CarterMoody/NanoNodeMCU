QUICK START (Assumes you have mqtt server up and running)    
  1. On NodeMcu (esp8266), load code MqttMotor.ino    
  2. On RPi, open a cmd launch .\forever3   
    1. Verify receiving heartbeats from the NodeMCU esp8266   
    2. Can now close this command prompt 
  3. Set up IP Camera and verify streaming    
  4. Goto youtube live dashboard and start a stream    
  5. Delete token.pickle if present (code will detect none exists, then ask you to re-authenticate).    
  6. On Rpi, open another cmd and launch YoutubeMqttNano.py via the forever script (simply execute ./forever3)    
    1. Follow authentication flow to get a new token.pickle (sign in and allow access)    
    2. Verify connection in terminal (should find correct broadcast id of your stream    
    3. Wait a minute or so for a heartbeat from the NodeMCU esp8266 (they come in every minute)    
  7. In youtube broswer, try sending "test !feed" in chat to dispense food.    
    1. Should see reaction in command prompt running YoutubeMqttNano.py    
    2. Should see mqtt message sent to NodeMCU esp8266    
    3. Should see mqtt message received from  NodeMCU esp8266    
    4. On youtube chat, should see RPi talking to user    
  8. Resync audio by running ./set64.sh and ./set48.sh which sends a request to the Dahua camera to switch audio sampling frequency, lining it back up (need to set a cron job to do this every 30 minutes! or else audio goes out of sync)    


To see list of running cronjobs:
	ps -o pid,sess,cmd afx | egrep -A20 "( |/)cron( -f)?$"
First column is PID, second column is SessionID, third column is command started by cron
To kill specific process find the PID associated with the crontab task at the lower (more root) level
pkill -s <PID FROM FIRST COLUMN>



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
  1. pdf - Shows API specific to my Dahua Live cam.    
  2. SSH and Curl - API examples    
  3. set48.sh - Sets Audio sampling frequency to 48000    
  4. set64.sh - Sets Audio sampling frequency to 64000    

MqttMotor\    
  1. MqttMotor.ino 
    - Connects to MQTT broker (RPI)    
    - sends heartbeats    
    - responds to MQTT messages    
    - spins motor    

RPi\    
  1. MqttServerPahoWorking.py 
    - Simple implementation of MQTT client in Python for testing.    
  2. YoutubeMqttNano.py     
    - Fully fledged program    
    - Connects to MQTT broker (RPI)    
    - listens for hearbeats from NodeMCU Arduino and responds with heartbeat Acknowledgement (ACK)    
    - sends MQTT messages    
    - Monitors NANO network via websocket    
    - Monitors Youtube Live chat via google API    
  3. forever REPLACED BY 'forever3' and 'myserver'     
    - simple bash program to cause infinite running of python program    
    - Needs work/research. shell=true is not safe.     
    - Requires python modules installed at sudo system-wide level.    
    - Should be switched to use pyenv    
    - Requires changing default OS python version to new python3 install    
  4. forever3 and myserver
    - Launch these by modifying as you see fit, then > ./forever3
  6. nodes.json    
    - list of nodes for Nano Websocket functionality    
  7. requirements.txt    
    - list of requirements for Nano Websocket functionality    
   
Testing\    
  1. mqttPahoSubClientWorking.ino    
    - very simple working Arduino code for MQTT client    



   
  

# Instructions: https://docs.google.com/document/d/11qHZTV_VtY0-6eIIvyDKzXHq9InnWSXJNmRCBqyEh5M/edit?usp=sharing


NOTE: When copy/pasting code from Windows, and unknown errors occur. Try the following commands to clean up newline characters:    
1. cat -v myfile      
2. tr -d '\r' < myfile > myfileNoBadCharacters    
