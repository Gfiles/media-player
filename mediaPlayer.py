import pathlib
import os
import platform
import sys
import requests #pip install requests
import json
import subprocess

VERSION = 20240727
# ---------- Functions ----------
def readConfig(settingsFile): 
    if os.path.isfile(settingsFile):
        with open(settingsFile) as json_file:
            data = json.load(json_file)
    else:
        data = {
            "doc" : "Configuration File Description",
            "versionFile" : "https://apps.ydreams.global/MediaPlayer/version.txt",
            "downloadContent" : False,
            "downloadURL" : "https://internaldev.ydreams.global/",
            "contentsURL" : "https://internaldev.ydreams.global/api/v1/app-data?appid=gex-8-2-estudio-jornalismo",
            "deleteOld" : True,
            "mediaFolders" : [
                "media"
            ],
            "Doc_videoPlayer" : "Video player commands for playing videos",
            "videoPlayer" : [
                "mpv",
                "-fs"
            ],
            "loopParameter" : "--loop",
            "fileTypes" : ["*.mp4", "*.mp3", "*.jpg", "*.png"]
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

def delete_files_in_directory(directory_path):
    try:
        files = os.listdir(directory_path)
        for file in files:
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print("All files deleted successfully.")
    except OSError:
        print("Error occurred while deleting files.")
     
def fnDownloadContents():
    # Read Download.json
    downloadFile = os.path.join(cwd, "download.json")
    if os.path.isfile(downloadFile):
        downloadConfig = readConfig(downloadFile)
        lastUpdate = downloadConfig["config"]["last_contents_update"]
    else:
        lastUpdate = ""
    #print(lastUpdate)

    print("Config file read")
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
    }

    #Start Downlading
    r = requests.get(url = contentsURL, headers = HEADERS)
    httpStatus = r.status_code
    if httpStatus == 200:
        #data = r.content
        jsonGet = r.text
        #print(jsonGet)
        # Serializing json
        jsonFile = os.path.join(cwd, "download.json")
        # Writing to config.json
        with open(jsonFile, "w") as outfile:
            outfile.write(jsonGet)
        jsonData = json.loads(jsonGet)
        newUpdate = jsonData["config"]["last_contents_update"]
        if lastUpdate != newUpdate:
            if deleteOld:
                delete_files_in_directory(mediaFolders[0])
            # Download Contents
            contents = jsonData["app"]["contents"]
            #check media folder
            for k, v in contents.items():
                #print(f"{k} - {v['pt']}")
                file_name = os.path.basename(v['pt']).lower()
                fileName = os.path.join(mediaFolders[0], file_name)
                print(fileName)
                downLoading = downloadURL + v['pt']
                print(downLoading)
                response = requests.get(downLoading)
                with open(fileName, mode="wb") as file:
                    file.write(response.content)
            print("Finished Downloading")
        else:
            print("media up to date")
    else:
        print(f"http Error: {httpStatus}")

def downloadVersionFile():
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
    }

    #Start Downlading
    r = requests.get(url = versionFile, headers = HEADERS)
    httpStatus = r.status_code
    if httpStatus == 200:
        versionOnline = int(r.text)
        print(f"{VERSION} < {versionOnline}")
        if VERSION >= versionOnline:
            print("Media Player up to Date")
        else:
            print("Downloading new Version.")

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
# ---------- End Functions ----------

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
print(OS)

# Read Config File
settingsFile = os.path.join(cwd, "config.json")
config = readConfig(settingsFile)
contentsURL = config["contentsURL"]
downloadContent = config["downloadContent"]
downloadURL = config["downloadURL"]
mediaFolders = config["mediaFolders"]
videoPlayer = config["videoPlayer"]
fileTypes = config["fileTypes"]
deleteOld = config["deleteOld"]
loopParameter = config["loopParameter"]
versionFile = config["versionFile"]

#Download Version File:
downloadVersionFile()
#Check if Folders existe and create if necessary

for i in range(len(mediaFolders)):
    mediaFolders[i] = os.path.join(cwd, mediaFolders[i])
    if not os.path.exists( mediaFolders[i]):
        os.mkdir( mediaFolders[i])

# Read Download.json
if downloadContent:
    fnDownloadContents()

#Play Media Files

#Get list of Files with especefic File Extensions
folder = pathlib.Path(os.path.join(cwd, mediaFolders[0]))
#patterns = ("*.mp4", "*.mp3", "*.jpg", "*.png", "*.MP4", "*.MP3", "*.JPG", "*.PNG")
patterns = ", ".join(fileTypes)

files = [f for f in folder.iterdir() if any(f.match(p) for p in patterns)]
numFiles = len(files)
print(files)
if numFiles == 0:
    running = False
    print("No Files to play. Closing...")
else:
    running = True
    #Teste if mpv Exists
    try:
        subprocess.run([videoPlayer[0]])
    except FileNotFoundError:
        running = installMediaPlayer()

try:
    while running:
        for file in files:
            print(file)
            fileExtension = file.suffix.lower()
            if fileExtension == ".mp4" or fileExtension == ".mp3":
                if numFiles == 1:
                    videoPlayer.append(loopParameter)
                    videoPlayer.append(file)
                    print(f"Play Video {videoPlayer}")
                    subprocess.run(videoPlayer)
                else:
                    videoPlayer.append(file)
                    subprocess.run(videoPlayer)
            elif fileExtension == ".jpg" or fileExtension == ".png":
                print("Play Image")
except KeyboardInterrupt:
    print("Canceled by User")
finally:
    # Close the serial connection to the Arduino
    killProcess(videoPlayer[0])