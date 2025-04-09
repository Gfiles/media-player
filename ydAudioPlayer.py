# pyinstaller --onefile -n rioCidadeEsporteAudio --noconsole muroAudioPlayer.py
import os
import sys
import requests #pip install requests
import json
import subprocess
import cv2 #pip install opencv-python
import numpy as np
import mimetypes
from time import sleep
import datetime
import psutil #pip install psutil

# ---------- Functions ----------
def readConfig(settingsFile): 
    if os.path.isfile(settingsFile):
        with open(settingsFile) as json_file:
            data = json.load(json_file)
    else:
        data = {
            "config": {
                "id": "volpi-labirinto-sensorial",
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
    try:
        if OS == "Windows":
            subprocess.run(["taskkill", "/IM", processName, "/F"])
        if OS == "Linux":
            if processName == "cvlc":
                subprocess.run(["pkill", "vlc"])
            else:
                subprocess.run(["pkill", processName])
    except:
        pass

def downloadContents(settingsFile):
    # Read Download.json
    config = readConfig(settingsFile)
    displayText("Reading Config File")
    lastUpdate = config["config"]["last_contents_update"]
    contents_url = config["config"]["contents_url"]
    id = config["config"]["id"]
    newUrl = contents_url.replace("\\", "")
    contentsURL = f"{newUrl}api/v1/app-data?appid={id}"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
    }

    #Start Downlading json
    print("Reading json file")
    try:
        displayText(f"Getting new Json file for id {id}")
        r = requests.get(url = contentsURL, headers = HEADERS)
        #print(f"request - {r}")
        httpStatus = r.status_code
    except:
        displayText("No Network Conection")
        httpStatus = "No network conection"
        jsonData = config

    if httpStatus == 200:
        jsonGet = r.text
        # Serializing json
        jsonFile = settingsFile
        # Writing to config.json
        with open(jsonFile, "w") as outfile:
            outfile.write(jsonGet)
        jsonData = json.loads(jsonGet)
        newUpdate = jsonData["config"]["last_contents_update"]
        lastUpdateDateTime = newUpdate
        displayText(f"Last update {lastUpdateDateTime}")
        # Download Contents
        contents = jsonData["app"]["contents"]
        newDownload = False
        for item in contents:
            for k, files in contents[item].items():
                fileName = os.path.join(mediaFolder, os.path.basename(files))
                if (lastUpdate != newUpdate) or (not os.path.isfile(fileName)):
                    downLoading = newUrl + files
                    displayText(f"Downloading {os.path.basename(files)}")
                    response = requests.get(downLoading)
                    with open(fileName, mode="wb") as file:
                        file.write(response.content)
                    lastUpdate = newUpdate
                    newDownload = True

                    #print(f"Finished Downloading {fileName}")
        if newDownload:
            displayText(f"Finished downloading files")
        else:
            displayText("Contents up to date")
    else:
        displayText(f"http Error: {httpStatus}")
    return jsonData

def installMediaPlayer():
    #install mpv
    print("Installing mpv")
    subprocess.run(["winget", "install", "mpv", "--disable-interactivity", "--nowarn", "--accept-package-agreements", "--accept-source-agreements"])
    print("Installation of MPV complete")
    return True

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

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        # Check if adding the next word would exceed the width
        test_line = f"{current_line} {word}".strip()
        text_size = cv2.getTextSize(test_line, font[0], font[1], font[2])[0]

        if text_size[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    # Add the last line
    lines.append(current_line)
    return lines

def displayText(text, duration=2):
    # Clear the image
    image[:] = (0, 0, 0)  # Black background
    # Put the text on the image
    #cv2.putText(image, text, (50, HEIGHT // 2), cv2.FONT_HERSHEY_SIMPLEX, 1, white, thickness, cv2.LINE_AA)
     # Wrap the text
    wrapped_lines = wrap_text(text, font, WIDTH - 100)

    # Display each line
    for i, line in enumerate(wrapped_lines):
        cv2.putText(image, line, (50, y0 + i * dy), font[0], font[1], (255, 255, 255), font[2], cv2.LINE_AA)

    # Show the image
    cv2.imshow(windowTitle, image)
    cv2.waitKey(duration * 1000)  # Wait for the duration in milliseconds
    #cv2.destroyAllWindows()

def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1:
            return
        yield start
        start += len(sub)

def isProcessRunning(processName):
    # Iterate over all running processes
    for proc in psutil.process_iter(['name']):
        try:
            # Check if process name matches
            if proc.info['name'] == processName:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False
         
# ---------- End Functions ----------

PROCESSTOCHECK = "mpv.exe"
killProcess(PROCESSTOCHECK)
# Open CV Settings
WIDTH, HEIGHT = 1280, 720
image = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
white = (255, 255, 255)
thickness = 2
windowTitle = "Muro Audio Player"
y0, dy = 100, 100  # Starting position and line height
font = (cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
 
displayText("App Started")
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
    
#check for folders and create if necessary
mediaFolder = os.path.join(cwd, "contents")
if not os.path.exists(mediaFolder):
    os.mkdir( mediaFolder)

# Config File Download
config = downloadContents(os.path.join(cwd, "appconfig.json"))

try:
    #check media folder
    contents = config["app"]["contents"]
    #check media folder
    fileNames = list()
    for item in contents:
        #print(item)
        for k, files in contents[item].items():
            fileNames.append(os.path.join(mediaFolder, os.path.basename(files)))
            break
    #print(fileName)
    running = True
except:
    displayText("Error Reading JSON File. Please delete json file to create a new one", 5)
    print("Error Reading JSON File")
    exit()

try:
    audioList = config["app"]["variables"]["audioDevices"]
    #print(audioList)
    audioDevices = audioList.split(",")
    print(audioDevices)
    displayText(f"Audio Devices {audioDevices}")
except:
    displayText("missing variable")
    audioDevices = ["(OUT 09-10", "(OUT 03-04", "(OUT 05-06", "(OUT 07-08"]

#find audio devices
audioList = subprocess.check_output(["mpv", "--audio-device=help"]).decode("utf-8")
print(audioList)
device = ""
deviceList = []
for i in audioList:
    device += i
    if i == "\n":
        deviceList.append(device)
        device = ""
wasapi = []
#Audio Devices for Channel
for audioDevice in audioDevices:
    for new in deviceList:
        if audioDevice in new:
            getDevice = list(find_all(new, "'"))
            wasapi.append(new[getDevice[0]+1: getDevice[1]])

print("--- wasapi List ---")
displayText(f"List of Devices on PC{wasapi}")
audioFiles = []
try:
    #check media folder
    contents = config["app"]["contents"]
    #check media folder
    for item in contents:
        #print(item)
        for k, files in contents[item].items():
            if check_file_type(files) == "audioFile":
                audioFiles.append(os.path.join(mediaFolder, os.path.basename(files)))
            break
    #print(fileName)
except:
    displayText("Error Reading JSON File. Please delete json file to create a new one", 5)
    exit()

# check if mpvinstalled
try:
    subprocess.run(PROCESSTOCHECK)
except Exception as e:
    print(f"mpv error: {e}")
    displayText("No mpv Installed, Installing MPV...")
    installMediaPlayer()

try:
    audioPlayerClean = config["audioPlayer"]
except:
    audioPlayerClean = ["mpv", "--title=mpvPlay", "--quiet", "--loop"]

startApps = True
try:
    while True:
        if startApps:
            displayText(f"Playing Audio files:\n{audioFiles[0]}")
            for i in range(len(audioFiles)):
                audioPlayer = audioPlayerClean.copy()
                audioPlayer.append(f"--audio-device={wasapi[i]}")
                audioPlayer.append(audioFiles[i])
                displayText(f"{audioPlayer}")
                subprocess.Popen(audioPlayer)
                sleep(2)

            #cv2.destroyAllWindows()
            startApps = False

        if not isProcessRunning(PROCESSTOCHECK):
            print(f"{PROCESSTOCHECK} is not running.")
            startApps = True

        #detect escape key and Windows close
        key = cv2.waitKey(1)  # Wait for 1 ms
        if key == 27:  # Escape key to break the loop
            break
        if cv2.getWindowProperty(windowTitle, cv2.WND_PROP_VISIBLE) < 1:
            break  # Window is closed

    killProcess(PROCESSTOCHECK)
    cv2.destroyAllWindows()
            
except KeyboardInterrupt:
    print("Canceled by User")
    killProcess(PROCESSTOCHECK)
    cv2.destroyAllWindows()
except IndexError:
    displayText("Audio device do not exsit on this PC Please install respective device", 5)
    killProcess(PROCESSTOCHECK)
    cv2.destroyAllWindows()