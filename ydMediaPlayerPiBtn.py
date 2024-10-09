#!/usr/bin/python3
"""
Raspberry Pinout https://www.raspberrypi.com/documentation/computers/images/GPIO-Pinout-Diagram-2.png?hash=df7d7847c57a1ca6d5b2617695de6d46

  29, 27,   25, 23,   21, 19,   17, 15
W-Or, Or, W-Gr, Bl, W-Bl, Gr, W-Br, Br 
 LED,   ,  Gnd,   ,  Btn,   , 3.3V,

https://raspberrypihq.com/use-a-push-button-with-raspberry-pi-gpio/
"""
import subprocess
import json
import os
import sys
import time
import requests #pip install requests
import RPi.GPIO as GPIO

def readConfig(settingsFile):
    if os.path.isfile(settingsFile):
        with open(settingsFile) as json_file:
            data = json.load(json_file)
    else:
        data = {
            "config": {
                "id": "la-fontaine-09-sala-leitura",
                "contents_url": "https:\/\/internaldev.ydreams.global\/",
                "last_contents_update": 0
            }
        }
        # Serializing json
        json_object = json.dumps(data, indent=4)
 
        # Writing to config.json
        with open(settingsFile, "w") as outfile:
            outfile.write(json_object)
    return data

def killProcess(process):
    subprocess.run(['pkill', process])
    
def downloadContents(settingsFile):
    # Read Download.json
    config = readConfig(settingsFile)
    lastUpdate = config["config"]["last_contents_update"]
    contents_url = config["config"]["contents_url"]
    id = config["config"]["id"]
    #print(lastUpdate)
    newUrl = contents_url.replace("\\", "")
    contentsURL = f"{newUrl}api/v1/app-data?appid={id}"
    #print(contentsURL)
    #print("Config file read"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
    }

    #Start Downlading json
    print(contentsURL)
    r = requests.get(url = contentsURL, headers = HEADERS)
    httpStatus = r.status_code
    if httpStatus == 200:
        jsonGet = r.text
        # Serializing json
        jsonFile = settingsFile
        # Writing to config.json
        with open(jsonFile, "w") as outfile:
            outfile.write(jsonGet)
        jsonData = json.loads(jsonGet)
        newUpdate = jsonData["config"]["last_contents_update"]
        # Download Contents
        contents = jsonData["app"]["contents"]
        for item in contents:
            for k, files in contents[item].items():
                fileName = os.path.join(mediaFolder, os.path.basename(files))
                if (lastUpdate != newUpdate) or (not os.path.isfile(fileName)):
                    downLoading = newUrl + files
                    print(downLoading)
                    response = requests.get(downLoading)
                    with open(fileName, mode="wb") as file:
                        file.write(response.content)
                    lastUpdate = newUpdate

            print("Finished Downloading")
        else:
            print("media up to date")
    else:
        print(f"http Error: {httpStatus}")
    return jsonData

# Get the current working
# directory (CWD)
killProcess('omxplayer')
try:
    this_file = __file__
except NameError:
    this_file = sys.argv[0]
this_file = os.path.abspath(this_file)
if getattr(sys, 'frozen', False):
    cwd = os.path.dirname(sys.executable)
else:
    cwd = os.path.dirname(this_file)

print("Current working directory:", cwd)

#check for folders and create if necessary
mediaFolder = os.path.join(cwd, "contents")
if not os.path.exists(mediaFolder):
    os.mkdir( mediaFolder)

# Config File Download
config = downloadContents(os.path.join(cwd, "appconfig.json"))
#print(config)
#contents_url = config["config"]["contents_url"]
#id = config["config"]["id"]

try:
    btnPin = int(config["app"]["variables"]["btnPin"])
    ledPin = int(config["app"]["variables"]["ledPin"])
except:
    print("missing variable")
    btnPin = 21
    ledPin = 13

try:
    rotate = config["app"]["variables"]["rotate"]
except:
    rotate = '0'

try:
    audioOut = config["app"]["variables"]["audioOut"]
except:
    audioOut = 'hdmi'
    
try:
    #check media folder
    contents = config["app"]["contents"]
    #check media folder
    fileNames = []
    for item in contents:
        #print(item)
        for k, files in contents[item].items():
            fileNames.append(os.path.join(mediaFolder, os.path.basename(files)))
            break
    #print(fileName)
    running = True

except:
    print("Error Reading JSON File")
    exit()
print(fileNames)
videoPlayer = ["omxplayer", "-o", audioOut, "--orientation", rotate]
#Create Loop video Session
videoPlayerLoop = videoPlayer.copy()
videoPlayerLoop.append("--loop")
videoPlayerLoop.append(fileNames[0])
subprocess.Popen(videoPlayerLoop)
#Create Video Play Session
videoPlayer.append("--layer")
videoPlayer.append("10")
videoPlayer.append(fileNames[1])

#setup  GPIO:
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(btnPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Set pin 26 to be an input pin and set initial value to be pulled up (high)
GPIO.setup(ledPin, GPIO.OUT, initial=GPIO.HIGH)

print("Ready")
running = True
try:
    while running:
        #print(GPIO.input(btnPin))
        if GPIO.input(btnPin) == GPIO.HIGH:
            GPIO.output(ledPin,GPIO.LOW)
            print("Button was pushed!")
            subprocess.run(videoPlayer)
            GPIO.output(ledPin,GPIO.HIGH)

except KeyboardInterrupt:
    GPIO.cleanup()
    killProcess('omxplayer')
