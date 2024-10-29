#!/usr/bin/python3
import subprocess
import json
import os
import sys
import requests #pip install requests
import platform

VERSION = 20241029
def readConfig(settingsFile):
    if os.path.isfile(settingsFile):
        with open(settingsFile) as json_file:
            data = json.load(json_file)
    else:
        data = {
            "config": {
                "id": "gex-10-1-patrocinadores",
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

def killProcess(processName):
    if OS == "Windows":
        subprocess.run(["taskkill", "/IM", processName, "/F"])
    if OS == "Linux":
        subprocess.run(["pkill", processName])

def getBackground():
    subprocess.Popen(["sudo", "apt", "install", "feh", "-y"], stdout = subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-i", fileNames[0], "-vf", 'select=1', "-vframes", "1", "-loglevel", "quiet", "background.png"], stdout = subprocess.DEVNULL)
    subprocess.Popen(["feh", "-F", "--hide-pointer", "background.png"])
    
def installMediaPlayer():
    if videoPlayer[0] == "mpv":
        #install mpv
        print("Installing mpv")
        if OS == "Windows":
            subprocess.run(["winget", "install", "mpv", "--disable-interactivity", "--nowarn", "--accept-package-agreements", "--accept-source-agreements"])
        if OS == "Linux":
            subprocess.run(["sudo", "apt", "install", "mpv", "-y"])
        print("Installation of MPV complete")
        return True
    else:
        print(f"Video Player is not installed, please install player {videoPlayer}, exiting...")
        return False
    
def downloadVersionFile():
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
    }

    #Start Downlading
    r = requests.get(url = versionFile, headers = HEADERS)
    httpStatus = r.status_code
    if httpStatus == 200:
        versionOnline = int(r.text)
        #print(f"{VERSION} < {versionOnline}")
        if VERSION >= versionOnline:
            print("Media Player up to Date")
        else:
            print("Downloading new Version.")

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
OS = platform.system()
killProcess('mpv')


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
    videoPlayer = config["app"]["variables"]["videPlayer"]
except:
    videoPlayer = ["mpv", "-fs"]

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
    sys.exit()

print(fileNames)
#Create Loop video Session
videoPlayerLoop = videoPlayer.copy()
videoPlayerLoop.append("--loop")
videoPlayerLoop.append(fileNames[0])
if len(fileNames) == 1:
    subprocess.run(videoPlayerLoop)
    sys.exit()
else:
    if OS == "Linux":
        getBackground()
    running = True

#Teste if mpv Exists
try:
    videoPlaying = subprocess.Popen([videoPlayer[0]], stdout = subprocess.DEVNULL) #do not show output
    videoPlaying.wait()
except FileNotFoundError:
    running = installMediaPlayer()
    
print("Ready")
try:
    while running:
        for videoFile in fileNames:
            videoPlay = videoPlayer.copy()
            videoPlay.append(videoFile)
            subprocess.run(videoPlay)

except KeyboardInterrupt:
    killProcess(videoPlayer[0])
    if OS == "Linux":
         killProcess("feh")
