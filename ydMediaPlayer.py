#!/usr/bin/python3
"""
Media File Keys:
    backGround -> Background media
BackOffice Variables:
    videoPlayer -> video player settings with parameters Ex: mpv -fs
    mpv -fs --loop
    cvlc -f --loop
    ffplay -fs -loop 0
    
"""
import subprocess
import json
import os
import sys
import requests #pip install requests
import platform

VERSION = 20250317
def readConfig(settingsFile):
    if os.path.isfile(settingsFile):
        with open(settingsFile) as json_file:
            data = json.load(json_file)
    else:
        data = {
            "config": {
                "id": "ydreams-video",
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
        if processName == "cvlc":
            subprocess.run(["pkill", "vlc"])
        else:
            subprocess.run(["pkill", processName])

def getBackground():
    subprocess.run(["ffmpeg", "-y", "-i", fileNames[0], "-vf", 'select=1', "-vframes", "1", "-loglevel", "quiet", "background.png"], stdout = subprocess.DEVNULL)
    return os.path.join(mediaFolder, "background.png")
    
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

def installFFmpeg():
    if OS == "Windows":
        subprocess.run(["winget", "install", "ffmpeg"])
    print("Installation of ffmpeg complete")
    return True
 
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
        else:
            print("media up to date")
        print("Finished Downloading")
    else:
        print(f"http Error: {httpStatus}")
    return jsonData

def check_file_type(file_path):
    # Guess the MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    #print(f"mime_type {mime_type} of {file_path}")
    if mime_type:
        if mime_type.startswith('audio'):
            return "audioFile"
        elif mime_type.startswith('video'):
            return "videoFile"
        else:
            return "This file is neither audio nor video."
    else:
        return "Could not determine the file type."

def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1:
            return
        yield start
        start += len(sub)

#---------- End Functions --------------

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

if OS == "Windows":
    killProcess("mpv.exe")
if OS == "Linux":
    killProcess("mpv")

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
try:
    videoPlayerGet = config["app"]["variables"]["videoPlayer"]
    videoPlayer = videoPlayerGet.split()
except Exception as error:
    print(f"Exception error: {error}, {OS}")
    if OS == "Windows":
        videoPlayer = ["mpv", "-fs"]
    if OS == "Linux":
        videoPlayer = ["cvlc", "-f", "--no-osd"]
#print(videoPlayer)

#Teste if mpv Exists
if videoPlayer[0] == "mpv":
	try:
		videoPlaying = subprocess.run([videoPlayer[0]], stdout = subprocess.DEVNULL) #do not show output
	except FileNotFoundError:
		running = installMediaPlayer()

try:
    #check media folder
    contents = config["app"]["contents"]
    #check media folder
    fileNames = []
    backGroundFile = ""
    for item in contents:
        #print(item)
        for k, files in contents[item].items():
            if item == "backGround":
                backGroundFile = os.path.join(mediaFolder, os.path.basename(files))
            else:
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
if videoPlayer == "ffplay":
    videoPlayerLoop.append("-loop")
    videoPlayerLoop.append("0")
else:
    videoPlayerLoop.append("--loop")
videoPlayerLoop.append(fileNames[0])
if len(fileNames) == 1:
    subprocess.run(videoPlayerLoop)
    sys.exit()
else:
    if backGroundFile == "":
        backGroundFile = getBackground()
    subprocess.Popen(["mpv", "-fs", "--loop", backGroundFile])
    running = True

#Teste if ffmpeg Exists
try:
    ffmpegTest = subprocess.Popen(["ffmpeg"], stdout = subprocess.DEVNULL) #do not show output
    ffmpegTest.wait()
except FileNotFoundError:
    running = installFFmpeg()
    
print("Ready")
try:
    while running:
        for videoFile in fileNames:
            videoPlay = videoPlayer.copy()
            videoPlay.append(videoFile)
            print(videoPlay)
            subprocess.run(videoPlay)

except KeyboardInterrupt:
    killProcess(videoPlayer[0])
    killProcess("mpv")
