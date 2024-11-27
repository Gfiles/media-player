#!/usr/bin/python3
import subprocess
import json
import os
import sys
import requests #pip install requests
import serial
import serial.tools.list_ports

def readConfig(settingsFile):
    if os.path.isfile(settingsFile):
        with open(settingsFile) as json_file:
            data = json.load(json_file)
    else:
        data = {
            "config": {
                "id": "la-fontaine-01-raposa-uvas",
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
killProcess('mpv')
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
settingsFile = os.path.join(cwd, "appconfig.json")
try:
    config = downloadContents(settingsFile)
except:
    config = readConfig(settingsFile)
    print("Internet Error")
#print(config)
#contents_url = config["config"]["contents_url"]
#id = config["config"]["id"]

usbName = "USB"
baudrate = 9600
uart = "auto"
useSerial = True
#Setup Serial
try:
    if uart == "auto":
        ports = list(serial.tools.list_ports.comports())
        #print(ports)
        for p in ports:
            if usbName in p.description:
                uart = p.device
        print(uart)
        ser = serial.Serial(
            # Serial Port to read the data from
            port = uart,
            #Rate at which the information is shared to the communication channel
            baudrate = baudrate,
            # Number of serial commands to accept before timing out
            timeout=1
        )
        
except Exception as error:
    print(error)
    print("No Serial")
    useSerial = False

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

#show Background Im'age
subprocess.run(["ffmpeg", "-y", "-i", fileNames[0], "-vf", 'select=1', "-vframes", "1", "-loglevel", "quiet", "background.png"], stdout = subprocess.DEVNULL)
subprocess.Popen(["mpv", "--loop", "-fs", os.path.join(mediaFolder, "background.png")], stdout = subprocess.DEVNULL)

try:
    videoPlayerGet = config["app"]["variables"]["videoPlayer"]
    videoPlayer = videoPlayerGet.split()
except Exception as error:
    print(f"Exception error: {error}, {OS}")
    if OS == "Windows":
        videoPlayer = ["mpv", "-fs"]
    if OS == "Linux":
        videoPlayer = ["cvlc", "-f", "--no-osd"]

print(fileNames)
#Create Loop video Session
videoPlayer.append("--loop")
videoPlayer.append(fileNames[0])
subprocess.Popen(videoPlayer)

print("Ready")

try:
    while useSerial:
        x = ser.readline().strip().decode()
        #print(x)
        if len(x) > 0:
            try:
                btnIn = int(x)
            except:
                btnIn = "" 
            if btnIn == 0:
                print("Button was pushed!")
                killProcess(videoPlayer[0])
                subprocess.Popen(videoPlayer)

except KeyboardInterrupt:
    ser.close()
    killProcess(videoPlayer[0])
    killProcess("mpv")