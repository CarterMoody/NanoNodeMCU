#!/usr/bin/env python

from enum import Enum  # Used for custom command Types from Youtube
import subprocess
import pytchat
import time
from time import sleep
from datetime import datetime, timezone
import pytz
import sys
from json import dumps, loads
import httplib2
from oauth2client.file import Storage
import cgi
import paho.mqtt.client as mqtt  # mqtt server stuff

PY3 = sys.version_info[0] == 3
if PY3:
    from urllib.parse import urlencode
    from queue import Queue
else:
    from Queue import Queue
    from urllib import urlencode

# Implementing blend with pytchat to prevent API quota limit
#video_id="8-oLIczRmaE" # pytchat used to use this but now we can get it with an api call in ytchat.py
# Trying to replace above line with call to youtube API to get Broadcast ID
#chat = pytchat.create(video_id="8-oLIczRmaE") Copied below in ### pytchat stuff ###

# allow shell execution of scripts launched from this file

## LiveChatID: 

### ytchat.py stuff ###
#from youtubechat import YoutubeLiveChat, get_live_chat_id_for_stream_now, get_broadcastId

# the name of the oauth credential file created by running the get_oauth_token.py in python-youtubechat
credential_file = "oauth_creds"

global livechat_id
global chat_obj
#######################

### pytchat stuff ###
global broadcastId  # NEEDS TESTING ONCE QUOTA RESETS
global pytchatObj
#sys.exit(); #prevent too many API calls idk
### MQTT Stuff ######
global client
#####################

my_channel_name = "Patagonian Duck"


# USER PLEASE CHANGE #
FEED_INTERVAL_SECONDS = 30  # Set this to amount of time before same user can
#    feed again 0 for instant
FEED_INTERVAL_MINUTES = 0  # Set to 0 to turn off
FEED_INTERVAL_HOURS = 0    # Set to 0 to turn off
FEED_INTERVAL_DAYS = 0     # Set to 0 to turn off
FEED_INTERVAL_TOTAL_SECONDS = FEED_INTERVAL_SECONDS \
    + (FEED_INTERVAL_MINUTES * 60) \
    + (FEED_INTERVAL_HOURS * 60 * 60) \
    + (FEED_INTERVAL_DAYS * 60 * 60 * 24)

# This Dictionary is to be maintained of all users who have issued commands
#       This will need to be expanded to allow for different timings on
#       different commands
# Key: UserName | Value: DateTimeObject representing time of last command
DAILY_USER_DICT = {}

native_dt = datetime.now()  # Reset Time to Local.. Not sure if needed pls test
print("printing native_dt")
print(native_dt)

# Get timezone/offset aware datetime
#CURRENT_DATE_TIME = datetime.now(pytz.utc)
CURRENT_DATE_TIME = datetime.now()


VALID_COMMANDS = ['!feed']

nano_receive_address = "nano_1ae75uxbfmpdqreejgziwut1ufj7e9othf1efo1byfocsjuoe63rtdmo1fg4"

#### Message Strings ####
msg_instruction = "Remember, you can feed at any time by sending ANY amount of $NANO to %s" % (
    nano_receive_address)

########### MQTT ###########################


def on_connect(client, userdata, flags, rc):
   printBetter("Connected with result code " + str(rc))
   # Subscribing in on_connect() means that if we lose the connection and
   # reconnect then subscriptions will be renewed.
   client.subscribe("/leds/pi")
# The callback for when a PUBLISH message is received from the server.


# Reacts to message received from client based on what bytes it receives in the payload
def on_message(client, userdata, msg):
    printBetter(msg.topic+" "+str(msg.payload))
    # Check if this is a message for the Pi LED.
    if msg.topic == '/leds/pi':
        # Look at the message data and perform the appropriate action.
        #if msg.payload == b'NANO_RECEIVED':
        #    GPIO.output(LED_PIN, GPIO.HIGH)
        messageString = str(msg.payload.decode("utf-8"))
        printBetter(f"received message: {messageString}")
        words = messageString.split()  # Split text on spaces
        if words[0] == 'nano_received':
            amount_received = words[1]
            responseMessage = "Received %s $NANO, Thanks a lot! Feeding now..." % (amount_received)
            send_chat(responseMessage)            
            


def mqtt_setup():
    global client
    # Create MQTT client and connect to localhost, i.e. the Raspberry Pi running
    # this script and the MQTT server.
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect('localhost', 1883, 60)
    # Connect to the MQTT server and process messages in a background thread.
    client.loop_start()
    # Main loop to listen for button presses.
    printBetter('Script is running, press Ctrl-C to quit...')
    time.sleep(3)


def mqtt_send(msg):
   printBetter(f"Sending message to esp8266: {msg}")
   #client.publish('/leds/esp8266', 'TOGGLE')
   client.publish('/leds/esp8266', msg)


def checkDictionary(key):
    global DAILY_USER_DICT

    updateDateTime()
    printBetter(f"checking dictionary for {key}")
    if key in DAILY_USER_DICT:
        # Check to see if they fed more than FEED_INTERVAL_MINUTES + FEED_INTERVAL_SECONDS ago
        timeUserLastFed = DAILY_USER_DICT.get(key)
        printBetter(f"{key} at time {timeUserLastFed}")
        #printBetter(f"Current time is:")
        #printBetter(CURRENT_DATE_TIME)

        return True

    else:
        printBetter(f"{key} not found in dictionary")
        return False


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
    timeUserLastFed = DAILY_USER_DICT.get(key)
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
    if (command == '!feed'):
        updateDateTime()
        #printBetter("successful !feed command... trying subprocess.call")
        #subprocess.call("/home/pi/Desktop/BirdFeeder/PythonScripts/StartFeedLoop.sh", shell=True)
        #printBetter(CURRENT_DATE_TIME)
        printBetter("*** *** *** *** ***")
        printBetter("successful !feed command... trying to send mqtt message")
        mqtt_send('RUNMOTOR')
        printBetter("*** *** *** *** ***")
        


# msg in this case is a LiveChatMessage object defined in ytchat.py
def respond(msg):
    msgTime = msg.datetime
    # Strip off TimeZone needed for comparison later
    #msgTimeNaive = timestamp_from_datetime(msgTime)
    msgAuthorName = msg.author.name
    msgText = msg.message
    printBetter(f"NEW MESSAGE: {msgTime} | {msgAuthorName} | {msgText}")

    # Check for presence of command
    commandsList = parseChatForCommands(msgText)
    if (commandsList):  # Check that list is not empty
        # Check for user in dictionary
        for command in commandsList:
            # Build a key based on Author's Name and Command Used
            key = msgAuthorName + command
            printBetter(f"key: {key}")
            dictionaryFound = checkDictionary(key)
            if (dictionaryFound):
                # Check if user has waited long enough to use this specific command
                timeRemaining = checkWaitedEnough(key, msgTime)
                if (timeRemaining == 0):
                    printBetter(
                        f"User: {msgAuthorName} has waited long enough for the {command} command")
                    # update dictionary with new time for this key (user + command)
                    DAILY_USER_DICT[key] = msgTime
                    richCommand(command, msgAuthorName)
                else:  # User has not waited long enough
                    printBetter(
                        f"User: {msgAuthorName} needs to wait {timeRemaining} more seconds before using the {command} command")
                    responseMessage = "Sorry %s, you must wait %d seconds before using the %s command again :)" % (
                        msgAuthorName, timeRemaining, command)
                    send_chat(responseMessage)
                    send_chat(msg_instruction)

            else:  # User + Command not found in dictionary
                DAILY_USER_DICT[key] = msgTime  # Add entry for user
                printBetter("feeding now")
                richCommand(command, msgAuthorName)

    else:  # Do nothing, no command found
        printBetter("no command found")

    #printBetter("PRINTING DICTIONARY")
    #print(DAILY_USER_DICT)
    #print("END DICTIONARY")

    #print(msg)
    #msg.delete()
    #chat_obj.send_message("RESPONSE!", chatid)


# May be useful for converting datetimes Not used currently
def datetime_from_timestamp(ts):
    return datetime.fromtimestamp(ts, pytz.utc).replace(tzinfo=None)


def timestamp_from_datetime(dt):
    return dt.replace(tzinfo=pytz.utc).timestamp()


def updateDateTime():
    #print("updating date time")
    global CURRENT_DATE_TIME
    #CURRENT_DATE_TIME = datetime.now(pytz.utc)
    CURRENT_DATE_TIME = datetime.now()


def build_chat_body(text):
    message = {
        u'snippet': {
            u'liveChatId': livechat_id,
            "textMessageDetails": {
                "messageText": text
            },
            "type": "textMessageEvent"
        }
    }

    jsondump = dumps(message)
    return jsondump


def send_chat(text):
    storage = Storage(credential_file)
    credentials = storage.get()
    body = build_chat_body(text)
    url = 'https://www.googleapis.com/youtube/v3/liveChat/messages'
    url = url + '?part=snippet'
    http = credentials.authorize(httplib2.Http())
    resp, data = my_json_request(http,
                                 url,
                                 'POST',
                                 headers={
                                     'Content-Type': 'application/json; charset=UTF-8'},
                                 body=body)
    return data


def my_json_request(http, url, method='GET', headers=None, body=None):
    resp, content = http.request(url, method, headers=headers, body=body)
    content_type, content_type_params = cgi.parse_header(
        resp.get('content-type', 'application/json; charset=UTF-8'))
    charset = content_type_params.get('charset', 'UTF-8')
    data = loads(content.decode(charset))
    if 'error' in data:
        error = data['error']
        raise YoutubeLiveChatError(
            error['message'], error.get('code'), error.get('errors'))
    return resp, data


def get_broadcastId(credential_file):
    # making this call: https://developers.google.com/youtube/v3/live/docs/liveBroadcasts/list
    storage = Storage(credential_file)
    credentials = storage.get()
    http = credentials.authorize(httplib2.Http())
    url = "https://www.googleapis.com/youtube/v3/liveBroadcasts?"
    params = {'part': 'id', 'broadcastStatus': 'active'}
    params = urlencode(params)
    resp, data = my_json_request(http, url + params)
    #print("request response: ")
    printBetter(data)
    # The broadcastID is inside the list of broadcasts, which is in the 'items'
    return data['items'][0]['id']


def get_live_chat_id_for_stream_now(credential_file):
    storage = Storage(credential_file)
    credentials = storage.get()
    http = credentials.authorize(httplib2.Http())
    url = "https://www.googleapis.com/youtube/v3/liveBroadcasts?"
    params = {'part': 'snippet', 'broadcastStatus': 'active'}
    params = urlencode(params)
    resp, data = my_json_request(http, url + params)
    #print("request response: ")
    #print(data)
    return data['items'][0]['snippet']['liveChatId']

class YoutubeLiveChatError(Exception):

    def __init__(self, message, code=None, errors=None):
        Exception.__init__(self, message)
        self.code = code
        self.errors = errors
        
        
# Generic wrapper to print which prints messages nicely with timestamp
def printBetter(String):
    global CURRENT_DATE_TIME
    updateDateTime()
    #print("|{}:{}:{}|{}".format(CURRENT_DATE_TIME.hour, CURRENT_DATE_TIME.minute, CURRENT_DATE_TIME.second, String), end='', flush=True)
    print("|{}:{}:{}|{}".format(CURRENT_DATE_TIME.hour, CURRENT_DATE_TIME.minute, CURRENT_DATE_TIME.second, String), flush=True)

def fillGlobals():
    global livechat_id
    global broadcastId
    global pytchatObj

    livechat_id = get_live_chat_id_for_stream_now(credential_file)
    printBetter(f"livechat_id: {livechat_id}")
    #print(livechat_id)
    #######################

    ### pytchat stuff ###
    # NEEDS TESTING ONCE QUOTA RESETS
    broadcastId = get_broadcastId(credential_file)
    printBetter(f"broadcastId: {broadcastId}")
    #print(broadcastId)
    #broadcastId = "Ww6QEItZtUs"
    pytchatObj = pytchat.create(video_id=broadcastId)
    #sys.exit(); #prevent too many API calls idk


def main():
    fillGlobals()  # Give values to global variables. Needs refactoring lol

    mqtt_setup()  # Setup mqtt server

    # pytchat stuff #####
    printBetter(f"Current feed Interval is {FEED_INTERVAL_TOTAL_SECONDS} seconds")
    if pytchatObj.is_alive():
        printBetter(f"monitoring chat on videoid {broadcastId}")
    else:
        printBetter(
            f"chat not alive for {broadcastId} check the v=VIDEO_ID is correct")
        exit()

    while pytchatObj.is_alive():
        #printBetter("first step in while loop")
        for msg in pytchatObj.get().sync_items():
            printBetter(f"{msg.datetime} {msg.author.name} {msg.message}")
            # for now, change msg.datetime to be current time in UTC
            updateDateTime()
            #print("done syncing date time")
            msg.datetime = CURRENT_DATE_TIME

            # Check if user used a command, and if it should feed
            #parseChat(c.datetime, c.author.name, c.message)
            if (msg.author.name == my_channel_name) and ("test" not in msg.message):  # Don't respond to myself
                printBetter("Message is from myself, continue")
                continue
            else:
                respond(msg)
                #text = "hello from carter pc"
                #send_chat(text)
        #printBetter("done syncing messages")
    if pytchatObj.is_alive():
        printBetter("still alive")
    printBetter("pytchatObj must no longer be alive, exiting")


if __name__ == '__main__':
    main()
