#!/bin/bash
# Frontdoor
URL="http://admin:PASSWORD@192.168.1.158/cgi-bin/configManager.cgi?action=setConfig&Encode[0].MainFormat[0].Audio.Frequency=48000"
# Remove spaces, otherwise url is invalid
URL=$(echo $URL | tr -d ' ')
# Send to cam
curl -g --user admin:PASSWORD --digest $URL