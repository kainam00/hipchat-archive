#!/usr/bin/env python2.7

import json, sys, getopt, calendar, time, os, requests
from pprint import pprint
from datetime import date

# Parse some args
helpstring = """Usage: {scriptname} args...
    Where args are:
        -h, --help    help. <this page>
        -i    (required) hostname of the hipchat endpoint to use. i.e. <organization>.hipchat.com
        -t    (required) access token to use. A HipChat Personal access token is the easiest way to do this - see https://www.hipchat.com/account/api
        -r    (required) room to download
        -d    (optional) date to start from in ISO format (YYYY-MM-DD). Defaults to current date
        -m    (optional) maximum number of messages to go back. Defaults to unlimited
        -v, --verbose

    Example: {scriptname} -i yourcompany.hipchat.com -t asdaASDasdasdad0120938123098 -r YOUR-TEAM-ROOM -d 2018-10-11 -m 2000 -v

"""

helpstring = helpstring.format(scriptname=sys.argv[0])

# Predefined variables
verbose = False
port = 443

# helper functions
def verboseOut(message):
    if verbose == True:
        print message 

class hipChat:
    def __init__(self, hostname, token):
        self.hostname = hostname
        self.token = token

    def getMessages(self, room, date, startIndex):
        try: 
            s = requests.Session()
            response = s.get('https://' + self.hostname + '/v2/room/' + room + '/history?auth_token=' + self.token + '&max-results=1000&date=' + startDate + '&start-index='+str(startIndex))
            verboseOut(response.text)
        except:
            print "CRITICAL - Unable to get response from " + hostname
            sys.exit(2)

        try:
            data = json.loads(response.text)
        except (ValueError):
            print "CRITICAL - Recieved invalid (non-JSON) response from " + hostname
            verboseOut(response.text)
            sys.exit(2)

        return data

# Parse args
try:
    options, remainder = getopt.getopt(sys.argv[1:], "d:h:i:t:r:m:v", ['help','verbose'])
except:
    print("Invalid args. Use -h or --help for help.")
    raise
    sys.exit(1)

for opt, arg in options:
    if opt in ('-h', '--help'):
        print helpstring
        sys.exit(0)
    elif opt in ('-i'):
        hostname = arg
    elif opt in ('-t'):
        token = arg
    elif opt in ('-r'):
        room = arg
    elif opt in ('-d'):
        startDate = arg
    elif opt in ('-m'):
        maxMessages = int(arg)
    elif opt in ('-v', '--verbose'):
        verbose = True

# Check to make sure the required variables are set.
try:
    hostname, token, room
except NameError:
    print("Invalid or missing args. Use -h or --help for help.")
    sys.exit(1)

try: 
    startDate
except NameError:
    startDate = date.today().isoformat()

try:
    maxMessages
except NameError:
    maxMessages = 9999999999999999

output = []
startIndex=0
session = hipChat(hostname, token)
messages = session.getMessages(room,startDate,startIndex)

# If the number of messages we recieved is greater than zero, keep repeating
counter = 0
try:
    while (len(messages['items']) > 0) and (startIndex < maxMessages):
        # write the current buffer into the output
        output.append(messages['items'])
        startIndex = startIndex+1000
        verboseOut("Got " + str(startIndex) + " messages from " + room)
        # Handle rate limiting, we're only allowed 500 requests in 5 mintutes
        # So if we're close to hitting the limit, wait 5 minutes and reset the counter
        if(counter >= 90):
            time.sleep(5*60+10)
            counter=0
        else:
            counter=counter+1
        messages = session.getMessages(room,startDate,startIndex)
except KeyError:
    print("ERROR: invalid json recieved. Maybe we're done? Or exceeded the rate limit? Counter: " + str(counter) + "\n")
    print messages

print json.dumps(output, indent=4, separators=(',',': '))
