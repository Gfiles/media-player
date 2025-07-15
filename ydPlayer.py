"""
Media File Keys:
    backGround -> Background media
BackOffice Variables:
    videoPlayer -> video player settings with parameters Ex: mpv -fs
    mpv -fs --loop
    cvlc -f --loop
    ffplay -fs -loop 0
    
"""
import mimetypes
import subprocess
import json
import os
import sys
import requests #pip install requests
import platform
from datetime import datetime
import shutil

VERSION = "2025.07.15"
print(f"Version : {VERSION}")

def download_and_replace(download_url):
    exe_path = sys.argv[0]
    tmp_path = exe_path + ".new"
    print(f"Downloading update from {download_url}...")
    r = requests.get(download_url, stream=True)
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(r.raw, f)
    print("Download complete.")
    # Create a batch file to replace the running exe after exit
    bat_path = exe_path + ".bat"
    with open(bat_path, "w") as bat:
        bat.write(f"""@echo off
ping 127.0.0.1 -n 3 > nul
move /Y "{tmp_path}" "{exe_path}"
start "" "{exe_path}"
del "%~f0"
""")
    print("Restarting with update...")
    os.startfile(bat_path)
    sys.exit(0)

def check_update(fileURL):
    getFileDate = get_modified_date(fileURL)
    if "An error occurred" in getFileDate or "No Last-Modified header found." in getFileDate:
        print(getFileDate)
        return
    
    newVersionDT = datetime.strptime(getFileDate, "%a, %d %b %Y %H:%M:%S %Z")
    versionDt = datetime.strptime(VERSION, "%Y.%m.%d")
    print(f"Current Version Date: {versionDt}")
    print(f"New Version Date: {newVersionDT}")
    if versionDt.date() < newVersionDT.date():
        print("Update available!")
        print(f"Download link: {fileURL}")
        download_and_replace(NEW_APP)
    else:
        print("You are using the latest version.")
        
def readConfig(settingsFile):
    if os.path.isfile(settingsFile):
        with open(settingsFile) as json_file:
            data = json.load(json_file)
    else:
        if OS == "Windows":
            updateApp = "https://proj.ydreams.global/ydreams/apps/ydPlayer.exe"
            mediaPlayer = "mpv -fs --osc=no --title=mpvPlay"
        elif OS == "Linux":
            updateApp = "https://proj.ydreams.global/ydreams/apps/ydPlayer"
            mediaPlayer = "cvlc -f --no-osd"
        data = {
            "mediaPlayer": mediaPlayer,
            "loopCmd": "--loop",
            "updateApp" : updateApp,
            "medias": [
                {
                    "fileUrl": "https://proj.ydreams.global/ydreams/videos/bunny_1080p_30fps.mp4",
                    "lastModified": ""
                }
            ]
        }
        # Serializing json
        json_object = json.dumps(data, indent=4)
 
        # Writing to config.json
        with open(settingsFile, "w") as outfile:
            outfile.write(json_object)
        print(f"Config file {settingsFile} created with default values.")
        getInput = input("Do you want to edit the config file? (y/n): ")
        if getInput.lower() == "y":
            if OS == "Windows":
                print("Opening config file in Notepad++")
                programFiles = os.getenv("ProgramFiles", "C:\\Program Files")
                notePadProgram = os.path.join(programFiles, "Notepad++", "notepad++.exe")
                subprocess.Popen([notePadProgram, settingsFile])
                
            elif OS == "Linux":
                subprocess.Popen(["geany", settingsFile])
            print("After editing, please restart the script.")
            sys.exit(0)
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
    
    medias = config.get("medias", [])
    fileName = medias[0].get("fileUrl", "")
    subprocess.run(["ffmpeg", "-y", "-i", fileName, "-vf", 'select=1', "-vframes", "1", "-loglevel", "quiet", "background.png"], stdout = subprocess.DEVNULL)
    return os.path.join(mediaFolder, "background.png")
    
def installMediaPlayer():
    if mediaPlayer[0] == "mpv":
        #install mpv
        print("Installing mpv")
        if OS == "Windows":
            subprocess.run(["winget", "install", "mpv", "--disable-interactivity", "--nowarn", "--accept-package-agreements", "--accept-source-agreements"])
        if OS == "Linux":
            subprocess.run(["sudo", "apt", "install", "mpv", "-y"])
        print("Installation of MPV complete")
        return True
    else:
        print(f"Video Player is not installed, please install player {mediaPlayer}, exiting...")
        return False

def installFFmpeg():
    if OS == "Windows":
        subprocess.run(["winget", "install", "ffmpeg"])
    print("Installation of ffmpeg complete")
    return True

def get_modified_date(url):
    try:
        response = requests.head(url)  # Use HEAD request to get headers
        if 'Last-Modified' in response.headers:
            return response.headers['Last-Modified']
        else:
            return "No Last-Modified header found."
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"
     
def saveConfigFile(configFile, config):
    # Serialize the config to a file
    jsonObject = json.dumps(config, indent=4)
    with open(configFile, 'w', encoding='utf-8') as f:
        f.write(jsonObject)
    print(f"Config saved to {configFile}")
    
def downloadContents():
    # Read Download.json
    #config = readConfig(settingsFile)
    medias = config.get("medias", [])
    
    for media in medias:
        print(media)
        mediaurl = media.get("fileUrl", "")
        mediaLastModified = media.get("lastModified", "")
        mediaDate = get_modified_date(mediaurl)
        #check if media is newer than lastModified
        #get file name from media URL
        fileName = os.path.basename(mediaurl)
        #print(f"File Name: {fileName}")
        filePath = os.path.join(mediaFolder, fileName)
        localMedias.append(filePath)
        print(f"File Path: {filePath}")
            
        if mediaDate != "No Last-Modified header found." and mediaDate != mediaLastModified:
            print(f"Media is newer than lastModified: {mediaDate} > {mediaLastModified}")
            print("Downloading Contents")
            lastUpdate = mediaDate
            r = requests.get(mediaurl, stream=True)
            with open(filePath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded {fileName} to {filePath}")
            media["lastModified"] = mediaDate
        else:
            print(f"Media up to date")
    
    saveConfigFile(settingsFile, config)
    print("Finished Downloading")

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
print(f"Operating System: {OS}")
if OS == "Windows":
    killProcess("mpv.exe")
if OS == "Linux":
    killProcess("mpv")

#check for folders and create if necessary
mediaFolder = os.path.join(cwd, "contents")
if not os.path.exists(mediaFolder):
    os.mkdir( mediaFolder)
localMedias = list()
# Config File Download
myName = os.path.splitext(os.path.basename(sys.argv[0]))[0]
#print(f"Script name: {myName}")
settingsFile = os.path.join(cwd, f"{myName}.json")
config = readConfig(settingsFile)
if OS == "Windows":
    NEW_APP = config.get("updateApp", "https://proj.ydreams.global/ydreams/apps/ydPlayer.exe")
elif OS == "Linux":
    NEW_APP = config.get("updateApp", "https://proj.ydreams.global/ydreams/apps/ydPlayer")
check_update(NEW_APP)
downloadContents()

if OS == "Windows":
    mediaPlayerGet = config.get("mediaPlayer", "mpv -fs")
elif OS == "Linux":
    mediaPlayerGet = config.get("mediaPlayer", "cvlc -f --no-osd")
mediaPlayer = mediaPlayerGet.split()

#Teste if mpv Exists
if mediaPlayer[0] == "mpv":
	try:
		videoPlaying = subprocess.run([mediaPlayer[0]], stdout = subprocess.DEVNULL) #do not show output
	except FileNotFoundError:
		running = installMediaPlayer()

#check number of files
if len(localMedias) == 0:
    print("No media files found, exiting...")
    sys.exit()
running = True

mediaPlayerLoop = mediaPlayer.copy()
mediaPlayerLoop.append(config.get("loopCmd", "--loop"))

print("Ready")
try:
    while running:
        if localMedias == 1:
            mediaPlayerLoop.append(localMedias[0])
            print(mediaPlayerLoop)
            subprocess.run(mediaPlayerLoop)
        else:
            #play all video in in loop
            for media in localMedias:
                player = mediaPlayer.copy()
                player.append(media)
                print(player)
                subprocess.run(player)
                
except KeyboardInterrupt:
    killProcess(mediaPlayer)
