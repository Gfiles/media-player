#!/usr/bin/python3
import json
import os
import sys
import subprocess
def readConfig(settingsFile):
    if os.path.isfile(settingsFile):
        with open(settingsFile) as json_file:
            data = json.load(json_file)
    else:
        data = {
            "videoFile" : "video.mp4",
            "videoPlayer" : ["mpv", "-fs", "--loop", "--no-osd"],
        }
        # Serializing json
        json_object = json.dumps(data, indent=4)
 
        # Writing to config.json
        with open(settingsFile, "w") as outfile:
            outfile.write(json_object)
    return data

def killProcess(processName):
    try:
        subprocess.run(["taskkill", "/IM", processName, "/F"])
        #print(f"killed process")
    except:
        print("No process to Kill")

#----------End Functions------------------

#----------Start Main---------------------
# Get the current working
# directory (CWD)
try:
    this_file = __file__
except NameError:
    this_file = sys.argv[0]
this_file = os.path.abspath(this_file)
if getattr(sys, 'frozen', False):
    cwd = os.path.dirname(sys.executable)
    bundle_dir = sys._MEIPASS
else:
    cwd = os.path.dirname(this_file)
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

print("Current working directory:", cwd)

settingsFile = os.path.join(cwd, "appConfig.json")
config = readConfig(settingsFile)
videoFile = os.path.join(cwd, config.get("videoFile", "video.mp4"))
videoPlayer = config.get("videoPlayer", ["mpv", "-fs", "--loop", "--no-osc"])
videoPlayer.append(videoFile)

runnning = os.path.isfile(videoFile)
print("Ready")
try:
    while runnning:
        
        subprocess.run(videoPlayer)
except KeyboardInterrupt:
    pass
killProcess("mpv.exe")
print("Exiting")
