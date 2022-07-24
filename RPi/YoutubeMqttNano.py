#!/usr/bin/env python

# Imports required from https://www.youtube.com/watch?v=vQQEaSnQ_bs
import os
import pickle
# Google's Request
from google.auth.transport.requests import Request
import requests # Python Request library used for HTTP requests and restarting the camera, setting sample rate
from requests.auth import HTTPDigestAuth
from google_auth_oauthlib.flow import InstalledAppFlow
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
## End new imports

from enum import Enum  # Used for custom command Types from Youtube
import subprocess
import pytchat
from pytchat import LiveChatAsync
import time
from time import sleep
from datetime import datetime, timezone, date, timedelta #datetime is both a library, AND a module. Not the whole library is imported here!
import pytz
import sys
from json import dumps, loads
import httplib2
from oauth2client import client
from oauth2client.file import Storage
import cgi
import paho.mqtt.client as mqtt  # mqtt server stuff


# From NanoWebsocket
import asyncio
import ssl
import websockets
import json
import random

global ssl_context
global nanoAddress
global nodes
global activeNode
global websocket
#####################

PY3 = sys.version_info[0] == 3
if PY3:
    from urllib.parse import urlencode
    from queue import Queue
else:
    from Queue import Queue
    from urllib import urlencode
    


##### New Credential Logic #####
credentials = None
youtubeAPI = None
# Edit to allow more access to the app
scopes=['https://www.googleapis.com/auth/youtube', 
        'https://www.googleapis.com/auth/youtube.force-ssl']
        

def build_youtubeAPI_object():
    global youtubeAPI
    youtubeAPI = googleapiclient.discovery.build(
        "youtube", "v3", credentials=credentials)

# Checks credentials. Tries to load from previous use, then checks them.
def check_credentials():
    printBetter("checking credentials")
    #printBetter("make sure you have a client_secrets.json")
    try_load_credentials()
    update_credentials()
    build_youtubeAPI_object()

# Tries to load in previously stored credentials
# token.pickle stores the user's credentials from previously successful logins
def try_load_credentials():
    global credentials
    if os.path.exists('token.pickle'):
        printBetter('Loading Credentials From File...')
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    else:
        printBetter("credentials file: 'token.pickle' not found")

# If there are no valid credentials available, then either refresh the token or log in.
#      Either way, creates/updates a file (token.pickle) with good credentials
def update_credentials():
    global credentials
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            printBetter('Refreshing Access Token...')
            credentials.refresh(Request())
        else:
            printBetter('Fetching New Tokens...')
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secrets.json',
                scopes
            )

            flow.run_local_server(port=8080, prompt='consent',
                                  authorization_prompt_message='')
            credentials = flow.credentials

            # Save the credentials for the next run
            with open('token.pickle', 'wb') as f:
                printBetter('Saving Credentials for Future Use...')
                pickle.dump(credentials, f)
##### End New Credential Logic #####
        

global livechat_id
global chat_obj
#######################

### pytchat stuff ###
global broadcastId  # NEEDS TESTING ONCE QUOTA RESETS
global pytchatObj
global pytchatObjAsync
#sys.exit(); #prevent too many API calls idk
### MQTT Stuff ######
global client
##################### # USER PLEASE CHANGE/ALTER/ADD ############

my_channel_name = "Patagonian Duck"

VALID_COMMANDS = ['!feed']

nano_receive_address = "nano_36zcuomrbm6mudwused38ptrofk43kmqphuprcxwxkomk647wgaq6ocsweyb"
minimimNanoThreshold = 0

FEED_INTERVAL_SECONDS = 30  # Set this to amount of time before same user can
#                               feed again, 0 for instant
FEED_INTERVAL_MINUTES = 0  # Set to 0 to turn off
FEED_INTERVAL_HOURS = 0    # Set to 0 to turn off
FEED_INTERVAL_DAYS = 0     # Set to 0 to turn off
FEED_INTERVAL_TOTAL_SECONDS = FEED_INTERVAL_SECONDS \
    + (FEED_INTERVAL_MINUTES * 60) \
    + (FEED_INTERVAL_HOURS * 60 * 60) \
    + (FEED_INTERVAL_DAYS * 60 * 60 * 24)

FEED_DAILY_MAXIMUM = 2 # Set this to the amount of maximum feedings per 24 hours per user. 0 for infinite NOT RECOMMENDED

#######################################################

# This Dictionary is to be maintained of all users who have issued commands
#       This will need to be expanded to allow for different timings on
#       different commands
# Key: String(msgAuthorName + command) | Value: Array of size FEED_DAILY_MAXIMUM of type DateTimeObject representing time of last command
DAILY_USER_DICT = {}


########### TIME ###########################
native_dt = datetime.now()  # Reset Time to Local.. Not sure if needed pls test
print("printing native_dt")
print(native_dt)

# Get timezone/offset aware datetime
#CURRENT_DATE_TIME = datetime.now(pytz.utc)
CURRENT_DATE_TIME = datetime.now()


#### Message Strings ####
msg_instruction = "Remember, you can feed at any time by sending ANY amount of $NANO to %s" % (
    nano_receive_address)
    
    

########### MQTT ###########################


def on_connect(client, userdata, flags, rc):
   printBetter("Connected with result code " + str(rc))
   # Subscribing in on_connect() means that if we lose the connection and
   # reconnect then subscriptions will be renewed.
   client.subscribe("#")
# The callback for when a PUBLISH message is received from the server.


# Reacts to message received from client based on what bytes it receives in the payload
def on_message(client, userdata, msg):
    #printBetter(msg.topic+" "+str( msg.payload)) 
    # Check if this is a message for the Pi LED.
    #printBetter("msg.topic: ")
    #printBetter(msg.topic)
    #printBetter("msg.payload: ")
    decoded_payload_string = msg.payload.decode() # Payload is originally a bytes object
    #printBetter(decoded_payload_string)
    printBetter("Received MQTT Message: " + "Topic: " + msg.topic + "Payload: " + decoded_payload_string)
    if msg.topic == 'nodemcu/heartbeat':
        #printBetter("msg.topic is nodemcu/heartbeat")
         # Look at the message data and perform the appropriate action. 
        if decoded_payload_string == "heartbeat": 
            #print("heartbeatAcknowledged")
            #printBetter('Sending message to esp8266')
            client.publish('nodemcu/heartbeatAcknowledged', 'heartbeatAcknowledged')
            
    # Show status of sensors NOT IMPLEMENTED YET
    if msg.topic == "/birdFeeder/status":
        if msg.payload == "1":
            printBetter("Topic: ", msg.topic + "\nMessage: " + str(msg.payload))
    if msg.topic == "/birdFeeder/status":
        if msg.payload == "0":
            printBetter("Topic: ", msg.topic + "\nMessage: " + str(msg.payload))
            


def mqtt_setup():
    global client
    # Create MQTT client and connect to localhost, i.e. the Raspberry Pi running 
    # this script and the MQTT server.
    mqtt_broker_ip = "localhost"
    client = mqtt.Client() 
    client.on_connect = on_connect 
    client.on_message = on_message 
    client.connect(mqtt_broker_ip, 1883, 60) 
    # Connect to the MQTT server and process messages in a background thread. (Non-blocking)
    client.loop_start()
    #client.loop_forever()
    # Main loop to listen for button presses. 
    printBetter('Script is running, press Ctrl-C to quit...') 
    time.sleep(3)


def mqtt_send(msg):
   printBetter(f"Sending message to esp8266: {msg}")
   client.publish('nodemcu/heartbeatAcknowledged', msg)


def checkDictionary(key):
    global DAILY_USER_DICT
    printBetter(f"checking dictionary for {key}")
    if key in DAILY_USER_DICT:
        # Check to see if they fed more than FEED_INTERVAL_MINUTES + FEED_INTERVAL_SECONDS ago
        timeUserLastFed = DAILY_USER_DICT.get(key[0]) #The first element in the array is the most recent feeding time
        printBetter(f"{key} at time {timeUserLastFed}")
        return True
    
    else:
        printBetter(f"{key} not found in dictionary")
        return False
    
    
    
# Handle the writing out and saving of the new dictionary
def writeOutDictionary():
    global DAILY_USER_DICT
    

# Rotates a list x places left or right
def rotate(input, n):
    return input[n:] + input[:n]


# Update dictionary to push on newest value, and pop off the oldest one, shifting everything over
def updateDictionary(key, msgTime):
    global DAILY_USER_DICT
    global FEED_DAILY_MAXIMUM
    logSize = FEED_DAILY_MAXIMUM
    
    userLog = DAILY_USER_DICT.get(key)
    # Rotate list over to the right once, and replace first value
    newUserLog = rotate(userLog, 1)
    newUserLog[0] = msgTime
    # newUserLog should now have an update log with the most recent X entries of feed times (X = FEED_DAILY_MAXIMUM)
    printBetter(f"newUserLog: {newUserLog}")
    DAILY_USER_DICT[key] = newUserLog
    #printBetter("PRINTING DICTIONARY")
    #print(DAILY_USER_DICT)
    #print("END DICTIONARY")
    writeOutDictionary()
    

# Create a new user in the dictionary
def newUser(key, msgTime):
    printBetter("key: " + key + " not found, creating new user entry")
    global DAILY_USER_DICT
    # Create at least of size 1
    if (FEED_DAILY_MAXIMUM == 0):
        keyArray = [None] * 1
    else:
        keyArray = [None] * FEED_DAILY_MAXIMUM    # Create new array for this user to hold their feeding times
        
    keyArray [0] = msgTime                        # Set first entry in their array to current time
    DAILY_USER_DICT[key] = keyArray               # Add entry for user
    writeOutDictionary()
    

# scan for all commands return a list
# emptylist on no commands found
def parseChatForCommands(msgText):
    commandsList = []
    words = msgText.split()  # Split text on spaces
    for word in words:
        word = word.lower()  # support both cases of given command
        if (word in VALID_COMMANDS):
            commandsList.append(word)

    return commandsList


def checkWaitedEnough(key, msgTime):
    userLog = DAILY_USER_DICT.get(key)
    timeUserLastFed = userLog[0]
    
    # Check difference between the Current time and timeUserLastFed
    #printBetter(f"CURRENT_DATE_TIME: {CURRENT_DATE_TIME}")
    printBetter(f"timeUserLastFed: {timeUserLastFed}")

    timediff = CURRENT_DATE_TIME - timeUserLastFed

    printBetter(f"Difference in time in days: {timediff.days}")
    timeDiffHoursCalculated = timediff.seconds / (60 * 60)
    printBetter(f"Difference in time in hours: {timeDiffHoursCalculated}")
    timeDiffMinutesCalculated = timediff.seconds / 60
    printBetter(f"Difference in time in  minutes: {timeDiffMinutesCalculated}")
    printBetter(f"Difference in time in seconds: {timediff.seconds}")

    if (timediff.seconds >= FEED_INTERVAL_TOTAL_SECONDS):
        timeRemaining = 0
        return timeRemaining
    else:
        timeRemaining = FEED_INTERVAL_TOTAL_SECONDS - timediff.seconds
        return timeRemaining


def richCommand(command, msgAuthorName):
    if (command == '!feed'):
        #responseMessage = "Thanks %s, I'm processing your %s command now!" % (
        #    msgAuthorName, command)
        responseMessage = "Thanks %s for feeding the birds!" % (msgAuthorName)
        send_chat(responseMessage)
        executeCommand(command)


def executeCommand(command):
    global client
    if (command == '!feed'):
        updateDateTime()
        #printBetter("successful !feed command... trying subprocess.call")
        #subprocess.call("/home/pi/Desktop/BirdFeeder/PythonScripts/StartFeedLoop.sh", shell=True)
        #printBetter(CURRENT_DATE_TIME)
        printBetter("*** *** *** *** ***")
        printBetter("successful !feed command... trying to send mqtt message")
        #mqtt_send('RUNMOTOR')
        client.publish('nodemcu/runmotor', 'runmotor')
        printBetter("*** *** *** *** ***")
        

# Checks to see if user has hit their maximum for today
#     Returns True if they have hit the daily limit
def hitDailyLimit(key, msgTime):
    global FEED_DAILY_MAXIMUM
    global DAILY_USER_DICT
    logSize = FEED_DAILY_MAXIMUM
    updateDateTime()
    
    # If the programmer set this to zero, there is no limit so always return False
    if FEED_DAILY_MAXIMUM == 0:
        return False
    
    userLog = DAILY_USER_DICT.get(key)
    # Check to see if last entry in array (oldest feed command entry) is greater than 1 day old or None
    oldestFeedTime = userLog[-1]
    #printBetter("PRINTING DICTIONARY")
    #print(DAILY_USER_DICT)
    #print("END DICTIONARY")
    #printBetter(f"oldestFeedTime: {oldestFeedTime}")
    if (oldestFeedTime == None):
        # User has not fed up to maximum
        return False
    

    # Check if oldestFeedTime is at least 24 hours old
    timeDelta = CURRENT_DATE_TIME - oldestFeedTime
    printBetter(f"timeDelta: {timeDelta}")
    if (timeDelta.days >= 1):
        return False
    else:
        return True
    
    
    
    


# Determine if user can feed or not, for whatever reason
def tailoredResponse(key, msgTime, msgAuthorName, command):
    timeRemaining = checkWaitedEnough(key, msgTime)
    dailyLimit = hitDailyLimit(key, msgTime)
    if dailyLimit:
        printBetter(f"User: {msgAuthorName} has reached their daily limit for the {command} command")
        responseMessage = "Sorry %s, you have reached your daily limit (%s) for the %s command, try again tomorrow :)" % (
            msgAuthorName, FEED_DAILY_MAXIMUM, command)
        send_chat(responseMessage)
        send_chat(msg_instruction)
        
    elif (timeRemaining == 0):
        printBetter(f"User: {msgAuthorName} has waited long enough for the {command} command")
        updateDictionary(key, msgTime)        # update dictionary with new time for this key (user + command)
        richCommand(command, msgAuthorName)   # fire off the command (probably !feed)
        
    else:  # User has not waited long enough
        printBetter(
            f"User: {msgAuthorName} needs to wait {timeRemaining} more seconds before using the {command} command")
        responseMessage = "Sorry %s, you must wait %d seconds before using the %s command again :)" % (
            msgAuthorName, timeRemaining, command)
        send_chat(responseMessage)
        send_chat(msg_instruction)



# msg in this case is a LiveChatMessage object defined in ytchat.py
def respond(msg):
    msgTime = msg.datetime
    msgAuthorName = msg.author.name
    msgText = msg.message

    # Check for presence of command
    commandsList = parseChatForCommands(msgText)
    if (commandsList):  # Check that list is not empty
        # Check for user in dictionary
        for command in commandsList:
            # Build a key based on Author's Name and Command Used
            key = msgAuthorName + command
            printBetter(f"key: {key}")
            dictionaryFound = checkDictionary(key)
            if (dictionaryFound): # User is in the dictionary
                # Check if user has waited long enough to use this specific command             
                tailoredResponse(key, msgTime, msgAuthorName, command)

            else:  # User + Command not found in dictionary
                newUser(key, msgTime)
                printBetter("feeding now")
                richCommand(command, msgAuthorName)


    else:  # Do nothing, no command found because commandsList is empty
        printBetter("no command found")

    #printBetter("PRINTING DICTIONARY")
    #print(DAILY_USER_DICT)
    #print("END DICTIONARY")
    #print(msg)



# May be useful for converting datetimes Not used currently
def datetime_from_timestamp(ts):
    return datetime.fromtimestamp(ts, pytz.utc).replace(tzinfo=None)
def timestamp_from_datetime(dt):
    return dt.replace(tzinfo=pytz.utc).timestamp()


def updateDateTime(timezone="local"):
    #print("updating date time")
    global CURRENT_DATE_TIME
    if timezone ==  "utc":
        CURRENT_DATE_TIME = datetime.now(pytz.utc)
    elif timezone == "local":
        CURRENT_DATE_TIME = datetime.now()


# Gets the current time, but returns it in the ISO-8601 Format
def get_iso8601_time(offset_sec=0, offset_minute=0, offset_hour=0, offset_day=0, offset_month=0, offset_year=0):
    global CURRENT_DATE_TIME
    utcTime = datetime.now(pytz.utc)
    today = date.today()
    todayString = "{}-{:02d}-{:02d}".format(today.year + offset_year, today.month + offset_month, today.day + offset_day)
    offsetTime = utcTime + timedelta(seconds = offset_sec)
        
    timeString = "T" + "{:02d}:{:02d}:{:02d}".format(offsetTime.hour, offsetTime.minute, offsetTime.second)
    iso8601String = todayString + timeString
    return iso8601String
    

# Read file into string
def readFile(filename):
    with open(filename, 'r') as file:
        data = file.read()
        return data
    
def setAudioSampleRate(frequency):
    username = readFile("CameraUsername.txt")
    password = readFile("CameraPassword.txt")
    url = "http://" + username + ":" + password + "@192.168.1.158/cgi-bin/configManager.cgi?action=setConfig&Encode[0].MainFormat[0].Audio.Frequency=" + frequency
    #url = "http://" + username + ":" + password + "@192.168.1.158/cgi-bin/configManager.cgi?action=reboot"
    r = requests.post(url, auth=HTTPDigestAuth(username, password))
    if r.status_code != 200:
        printBetter("Request to toggle IP Camera audio has failed!")
        printBetter(r)    

# Toggle Dahua IP Camera Audio back and forth, to tickle the YouTube stream ingestion point and hopefully start
def toggleIPCameraAudio():
    printBetter("Toggling Camera Audio")
    setAudioSampleRate("48000")
    sleep(5)
    setAudioSampleRate("64000")
    sleep(5)
    return 1


# Start Live Broadcast VIA YouTubeAPI
# https://developers.google.com/youtube/v3/live/docs/liveBroadcasts/insert
def start_livestream():
    printBetter("start_livestream")
    offset_sec = 10 # Set start time to 10 seconds from now
    startTime = get_iso8601_time(offset_sec=15)
    startTimeStr = str(startTime)
    #endTime = get_iso8601_time(offset_year=1)   # Not apparently necessary, no end time provided = infinite stream
    printBetter(f"startTime: {startTime}")
    #printBetter(f"endTime: {endTime}")
    titleStr = "Live Interactive Bird Feeder Arizona"
    descriptionStr = readFile("liveStreamDescription.txt")
    request = youtubeAPI.liveBroadcasts().insert(
        part="snippet, contentDetails,status",
        body={
          "contentDetails": {
            "enableAutoStart": True,
            "enableClosedCaptions": False,
            "enableContentEncryption": True,
            "enableDvr": True,
            "enableEmbed": True,
            "recordFromStart": True,
            "startWithSlate": True,
            "latencyPreference": "low",
          },
          "snippet": {
            "title": titleStr,
            "description": descriptionStr,
            "scheduledStartTime": startTimeStr,
          },
          "status": {
            "privacyStatus": "public"
          }
        }
    )
    response = request.execute()
    #print(response)   

# Send Chat VIA YouTubeAPI
# https://developers.google.com/youtube/v3/live/docs/liveChatMessages/insert?apix=true
def send_chat(text):
    #print("send_chat: " + text)
    request = youtubeAPI.liveChatMessages().insert(
        part="snippet",
        body={
          "snippet": {
            "liveChatId": livechat_id,
            "type": "textMessageEvent",
            "textMessageDetails": {
              "messageText": text
            }
          }
        }
    )
    response = request.execute()
    #print(response)    


# Get BroadcastID VIA YouTubeAPI
#   The BroadcastID is the short alphanumeric code which identifies the video
#   and appears in the url of the video
# https://developers.google.com/youtube/v3/live/docs/liveBroadcasts/list
def get_broadcastId():
    #print("get_broadcastId")
    request = youtubeAPI.liveBroadcasts().list(
        part="id",
        broadcastStatus="active"
    )
    response = request.execute()
    
    #print(response)
    return response['items'][0]['id']
    
    
# Returns YouTube LiveChatID. This is different from the BroadcastID because:
#    It identifies the current chat attached to the BroadcastID
#    I'm not sure how often, but it is subject to change while the BroadcastID
#    remains the same.
# # https://developers.google.com/youtube/v3/live/docs/liveBroadcasts/list
def get_live_chat_id_for_stream_now():
    #print("get_live_chat_id_for_stream_now")
    request = youtubeAPI.liveBroadcasts().list(
        part="snippet",
        broadcastStatus="active"
    )
    response = request.execute()
    
    #print(response)
    try:
        return response['items'][0]['snippet']['liveChatId']
    except:
        printBetter("Error on getting live_chat_id, are you streaming?")
        return 69
    
# Going to check and make sure stream is running
def get_live_chat_id():
    livechat_id = get_live_chat_id_for_stream_now()
    while ( livechat_id == 69 ): # Failed to find livechat, need to try to launch a new livestream
        start_livestream()
        sleep(120) # Give the camera time to start up. This value is technically smaller, as livestream has an offset
        toggleIPCameraAudio()
        printBetter("Camera Audio Toggled")
        sleep(30) # Give YouTube some time to connect the stream, and go live
        livechat_id = get_live_chat_id_for_stream_now()
        sleep(5)
    return livechat_id
         
        
# Generic wrapper to print which prints messages nicely with timestamp
def printBetter(String):
    global CURRENT_DATE_TIME
    updateDateTime()
    #print("|{}:{}:{}|{}".format(CURRENT_DATE_TIME.hour, CURRENT_DATE_TIME.minute, CURRENT_DATE_TIME.second, String), end='', flush=True)
    print("|{:02d}:{:02d}:{:02d}|{}".format(CURRENT_DATE_TIME.hour, CURRENT_DATE_TIME.minute, CURRENT_DATE_TIME.second, String), flush=True)

def fillGlobalsPytChatObj():
    global livechat_id
    global broadcastId
    global pytchatObj

    #livechat_id = get_live_chat_id_for_stream_now(credentials)
    livechat_id = get_live_chat_id()
    printBetter(f"livechat_id: {livechat_id}")

    #print(livechat_id)

    broadcastId = get_broadcastId()
    printBetter(f"broadcastId: {broadcastId}")
    #print(broadcastId)
    pytchatObj = pytchat.create(video_id=broadcastId)
    #pytchatObjAsync = LiveChatAsync(video_id=broadcastId, callback = pytchat_check)



def raw_to_nano(raw): #This is NOT the correct way to do this (floating point error) but for now it will do for testing.
    return (int(raw) / 1000000000000000000000000000000)
def nano_to_raw(raw): #Read comment above:
    return (int(raw) * 1000000000000000000000000000000)

def load_nodes(): #Load nodes.json file with all nodes (websocket addresses)
    global nodes
    printBetter("Loading list of nodes from file...")
    with open("nodes.json", "r") as file:
        nodes = json.load(file)
        printBetter("Nodes loaded.")

def assign_random_node(): #Assign node randomly.
    global activeNode
    printBetter("Assigning random node...")
    load_nodes()
    activeNode = nodes["nodes"][random.randint(0, len(nodes))]
    printBetter(f"Node assigned! ({activeNode})")
    
def websocket_initial_setup(): # Used to be run globally
    global ssl_context
    global nodes
    global activeNode

    
    ssl_context = ssl.create_default_context() #Create SSL default cert. (websocket is TLS)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    nodes = [] #In the future i want the ability to switch node. In case of an offline node. Thats why this is global.

    activeNode = "" #a node (websocket) will be randomly assigned to this string and used.
    # Exception logic
    #try:
    assign_random_node() # Assign random socket node from file.
    #asyncio.run(websocket_setup_listen())

async def websocket_setup_listen(): #Connect to websocket. Subscribe and listen for transactions.
    global websocket
    global client
    printBetter("doing the websocket thing")
    async with websockets.connect(activeNode, ssl=ssl_context) as websocket:
        printBetter(f"Connected to websocket: {activeNode}\nSending subscription to websocket.")
        await websocket.send('{"action": "subscribe","topic": "confirmation","options":{"accounts": ["' + nano_receive_address + '"]}}') #F strings don't work :(
        print(await websocket.recv())
        printBetter("Subscribed!\nNow waiting for donations...\n\n")


    
        while 1: #Infinite listen loop. Listen for transactions
            rec = json.loads(await websocket.recv()) #Get JSON transaction payload

            #PUT YOUR LOGIC HERE!!!!
            if "send" in rec["message"]["block"]["subtype"] and nano_receive_address not in rec['message']['account']: #If its a donation (if type is send). Print. usefull for Twitch bot integration.
            
                confirmation = rec.get("topic", None) #Check if topic key exists. If not, make None.
                if confirmation: #check if None.
                    if confirmation == "confirmation": #Send NANO is legit and confirmed.
                        accountAddress = rec['message']['account']
                        amountRaw = rec['message']['amount']
                        amountNANO = raw_to_nano(rec['message']['amount'])
                        printBetter(f"GOT DONATION FROM {accountAddress}\nAmount RAW: {amountRaw}\nAmount NANO: {amountNANO}")
                        if (int(amountRaw) > minimimNanoThreshold):
                            printBetter("*** *** *** *** ***")
                            printBetter("successful Nano donation... trying to send mqtt message")
                            client.publish('nodemcu/runmotor', 'runmotor')
                            printBetter("*** *** *** *** ***")
                            responseMessage = "Received %s $NANO, Thanks a lot! Feeding now..." % (amountNANO)
                            send_chat(responseMessage)    
                        




# Adapted from here: https://github.com/taizan-hokuto/pytchat/wiki/LiveChatAsync
# callback function is automatically called periodically
async def pytchat_check():
    while 1:
        if pytchatObj.is_alive():
            for msg in pytchatObj.get().sync_items():
                #printBetter(f"NEW MESSAGE: {msg.datetime} {msg.author.name} {msg.message}")
                printBetter(f" NEW MESSAGE: {msg.datetime} | {msg.author.name} | {msg.message}")
                
                # This should ensure datetime of the message is in your current timezone, but will overwrite actual message time
                updateDateTime()
                msg.datetime = CURRENT_DATE_TIME

                # Check if user used a command, and if it should feed
                if (msg.author.name == my_channel_name) and ("test" not in msg.message):  # Don't respond to myself
                    printBetter("Message is from myself, continue")
                    continue
                else:
                    respond(msg)
                #await chatdata.tick_async()
            await asyncio.sleep(1)
    
        
        else:
            # pytchatObj must not be alive anymore, try to reconnect
            sleep(3)
            printBetter("pytchatObj is not alive anymore... trying to create again...")
            #Handle gracefully without restart...
            #fillGlobalsPytChatObj()
            exit()
    


  
  
def launch_async_tasks():
    websocket_initial_setup()
    
    # New Async stuff from https://stackoverflow.com/questions/31623194/asyncio-two-loops-for-different-i-o-tasks
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(pytchat_check())
        #loop.create_task(websocket_setup_listen())
        
        loop.run_until_complete(websocket_setup_listen())
        #loop.run_forever(pytchat_check())
        #loop.run_forever()
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
    
if __name__ == "__main__":
    check_credentials()
    #start_livestream()
    #restartIPCamera()
    fillGlobalsPytChatObj()  # Give values to global variables. Needs refactoring lol
    mqtt_setup()  # Setup mqtt server
    launch_async_tasks()
    
    # Adding loop to test mqtt
    #while(1):
    #    print("mqtt running")
    #    sleep(5)
