"""
Media File Keys:
	backGround -> Background media
BackOffice Variables:
	videoPlayer -> video player settings with parameters Ex: mpv -fs
	mpv -fs --loop
	cvlc -f --loop
	ffplay -fs -loop 0
	aplay -l to get list of audio devices
	aplay -Dplughw:2,0
pyinstaller --onefile -n ydPLayer_arm64 ydPlayer.py
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
import signal

VERSION = "2025.08.20"
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
			updateApp = "https://proj.ydreams.global/ydreams/apps/ydPlayer_arm64"
			mediaPlayer = "cvlc -f --no-osd --play-and-exit -q"
		data = {
			"mediaPlayer": mediaPlayer,
			"playAllAtOnce" : False,
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
	# loop through the medias to find the first video file
	for media in localMedias:
		if check_file_type(media) == "videoFile":
			backGroundFile = os.path.join(mediaFolder, "background.png")
			print(f"Creating background file: {backGroundFile} from {media}")
			subprocess.run(["ffmpeg", "-y", "-i", media, "-ss", "00:00:01", "-vframes", "1", "-loglevel", "quiet", backGroundFile], stdout = subprocess.DEVNULL)
			return backGroundFile
	return None

def installMediaPlayer(appToInstall):
	if appToInstall == "mpv":
		#install mpv
		print("Installing mpv")
		if OS == "Windows":
			subprocess.run(["winget", "install", "mpv", "--disable-interactivity", "--nowarn", "--accept-package-agreements", "--accept-source-agreements"])
		if OS == "Linux":
			subprocess.run(["sudo", "apt", "install", "mpv", "-y"])
		print("Installation of MPV complete")
		return True
	else:
		print(f"Video Player is not installed, please install player {appToInstall}, exiting...")
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
		downLoadFile = False
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
		if not os.path.isfile(filePath):
			downLoadFile = True
		if mediaDate != "No Last-Modified header found." and mediaDate != mediaLastModified:
			downLoadFile = True
		if downLoadFile:
			print("Downloading Contents")
			r = requests.get(mediaurl, stream=True)
			totalSize = int(r.headers.get('content-length', 0))
			downloadedSize = 0
			with open(filePath, 'wb') as f:
				for chunk in r.iter_content(chunk_size=8192):
					f.write(chunk)
					downloadedSize += len(chunk)
					done = int(50 * downloadedSize / totalSize)
					sys.stdout.write(f'\r[{"#" * done}{"-" * (50 - done)}] {downloadedSize / 1048576:.2f} MB / {totalSize / 1048576:.2f} MB')
					sys.stdout.flush()
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

def check_internet(url):
	try:
		response = requests.get(url, timeout=5)
		return True if response.status_code == 200 else False
	except requests.ConnectionError:
		return False

def signal_handler(sig, frame):
	if sig == 15:
		print('Received Close signal')
	else:
		print('Received signal:', sig)
	killProcess(mediaPlayer[0])
	if OS == "Linux":
		killProcess("mpv")
	elif OS == "Windows":
		killProcess("mpv.exe")
	sys.exit(0)
    
#---------- End Functions --------------

# Register the signal handler
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)  # Optional: Handle Ctrl+C

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

if check_internet(NEW_APP):
	check_update(NEW_APP)
	downloadContents()
else:
	medias = config.get("medias", [])
	for media in medias:
		mediaurl = media.get("fileUrl", "")
		fileName = os.path.basename(mediaurl)
		filePath = os.path.join(mediaFolder, fileName)
		localMedias.append(filePath)

if OS == "Windows":
	mediaPlayerGet = config.get("mediaPlayer", "mpv -fs")
elif OS == "Linux":
	mediaPlayerGet = config.get("mediaPlayer", "cvlc -f --no-osd")
mediaPlayer = mediaPlayerGet.split()

#Teste if mpv Exists
try:
	videoPlaying = subprocess.run(["mpv"], stdout = subprocess.DEVNULL) #do not show output
except FileNotFoundError:
	if installMediaPlayer("mpv") == False:
		input("mpv not installed, Please install manually, exiting...")
		sys.exit()

#Teste if ffmpeg Exists
try:
	subprocess.run(["ffmpeg"], stdout = subprocess.DEVNULL) #do not show output
except FileNotFoundError:
	installFFmpeg()

#check number of files
if len(localMedias) == 0:
	input("No media files found, exiting...")
	sys.exit()
running = True

#Check if File Exists and remove item if none exists
localMediasCopy = localMedias.copy()
localMedias = list()
for filePath in localMediasCopy:
	if os.path.isfile(filePath):
		localMedias.append(filePath)

#Play background in loop
if len(localMedias) > 1:
	backGroundFile = getBackground()
	if backGroundFile:
		print(f"Background file: {backGroundFile}")
		backGroundPlayer = ["mpv", "-fs", "--osc=no", "--loop", "--title=mpvPlay"]
		backGroundPlayer.append(backGroundFile)
		print(f"Media Player Command: {backGroundPlayer}")
		subprocess.Popen(backGroundPlayer, stdout = subprocess.DEVNULL)

playAllAtOnce = config.get("playAllAtOnce", False)
#Create players Processes
if playAllAtOnce:
	multiPlayers = list()
	players = list()
	for media in localMedias:
		player = mediaPlayer.copy()
		player.append(media)
		players.append(player)
		print(player)
		multiPlayers.append(subprocess.Popen(player))
print("Ready")
while running:
	#play all medias in loop
	for i, media in enumerate(localMedias):
		if playAllAtOnce:
			if multiPlayers[i].poll() is not None:
				print(players[i])
				multiPlayers[i] = subprocess.Popen(players[i])
		else:
			player = mediaPlayer.copy()
			player.append(media)
			print(player)
			subprocess.run(player)
