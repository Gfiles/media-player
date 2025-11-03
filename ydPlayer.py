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
Windows:
	.venv\Scripts\pyinstaller --onefile --add-data "devcon.exe;." -n ydPlayer ydPlayerNew.py
Rasp Pi:
	.venv/bin/pyinstaller --onefile -n ydPlayerBtns_arm64 ydPlayerNew.py
"""
import mimetypes
import subprocess
import time
import json
import os
import sys
import requests #pip install requests
import platform
from datetime import datetime
import shutil
import signal
import serial.tools.list_ports
import random
from urllib.parse import urlparse
from inputimeout import inputimeout, TimeoutOccurred #pip install inputimeout
from pystray import MenuItem as item, Icon as icon #pip install pystray
from PIL import Image #pip install pillow
import threading
import ctypes

VERSION = "2025.01.15"
print(f"Version : {VERSION}")

def download_and_replace(download_url):
	global OS
	exe_path = sys.argv[0]
	tmp_path = exe_path + ".new"
	print(f"Downloading update from {download_url} ...")
	r = requests.get(download_url, stream=True)
	with open(tmp_path, "wb") as f:
		shutil.copyfileobj(r.raw, f)
	print("Download complete.")
	# Create a batch file to replace the running exe after exit
	if OS == "Windows":
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

	if OS == "Linux":
		bat_path = exe_path + ".sh"
		with open(bat_path, "w") as bat:
			bat.write(f"""#!/bin/bash
sleep 3
mv -f "{tmp_path}" "{exe_path}"
"./{exe_path}"
""")
		os.chmod(tmp_path, 0o755)
		print("Restarting with update...")
		os.system(f"sh {bat_path}")

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
		#Teste if mpv Exists
		installApps()
		try:
			videoPlaying = subprocess.run(["mpv"], stdout = subprocess.DEVNULL) #do not show output
		except FileNotFoundError:
			try:
				user_input = inputimeout(prompt="mpv not installed, Please install manually, exiting...", timeout=60)
				print(f'You entered: {user_input}')
			except TimeoutOccurred:
				print('Time is up! Continuing with the script...')
			sys.exit(0)

		# --- Architecture-specific modifications ---
		machine_arch = platform.machine().lower()
		if sys.platform.startswith('win'):
			updateApp = "https://proj.ydreams.global/ydreams/apps/ydPlayer.exe"
			mediaPlayer = "mpv.exe -fs --volume=100 --osc=no --title=mpvPlay"
			usbName = "CH340"
		elif machine_arch in ('aarch64', 'arm64'):
			updateApp = "https://proj.ydreams.global/ydreams/apps/ydPlayer_arm64"
			mediaPlayer = "cvlc -f --no-osd --play-and-exit -q"
			usbName = "USB"
		elif sys.platform.startswith('linux') and machine_arch in ('x86_64', 'i686', 'x86'):
			updateApp = "https://proj.ydreams.global/ydreams/apps/ydPlayer_deb"
			mediaPlayer = "mpv.exe -fs --volume=100 --osc=no --title=mpvPlay"
			usbName = "USB"

		data = {
				"uart" : "auto",
				"useSerial" : False,
				"baudrate" : 9600,
				"usbName" : usbName,
				"updateApp" : updateApp,
				"playAllAtOnce" : False,
				"playRandom" : False,
				"medias": [
					{
						"mediaPlayer": mediaPlayer,
						"audioOut" : "auto",
						"fileUrl": "https://proj.ydreams.global/ydreams/videos/no_app.mp4",
						"lastModified": ""
					}
				]
			}
		if sys.platform.startswith('win'):
			data["arduinoDriver"] = "USB\\VID_1A86&PID_7523"
			
		# Serializing json
		json_object = json.dumps(data, indent=4)
 
		# Writing to config.json
		with open(settingsFile, "w") as outfile:
			outfile.write(json_object)
		print(f"Config file {settingsFile} created with default values.")
		try:
			getInput = inputimeout(prompt="Do you want to edit the config file? (y/n): ", timeout=60)
			print(f'You entered: {getInput}')
		except TimeoutOccurred:
			print('Time is up! Continuing with the script...')
			getInput = ""
		if getInput.lower() == "y":
			open_config_file()
			print("After editing, please restart the script.")
			sys.exit(0)
	return data

def killProcess(processName):
	# Extract just the executable name if a path is provided
	process_base_name = os.path.basename(processName)
	if OS == "Windows":
		# Add .exe if not present for Windows taskkill
		if not process_base_name.lower().endswith('.exe'):
			process_base_name += '.exe'
		subprocess.run(["taskkill", "/IM", process_base_name, "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	if OS == "Linux":
		if process_base_name == "cvlc":
			subprocess.run(["pkill", "vlc"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		else:
			subprocess.run(["pkill", process_base_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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

def installApps():
	try:
		#install mpv
		if OS == "Windows":
			if not shutil.which("mpv"):
				print("Installing mpv")
				subprocess.run(["winget", "install", "mpv", "--accept-package-agreements", "--accept-source-agreements"])
			if not shutil.which("ffmpeg"):
				print("Installing ffmpeg")
				subprocess.run(["winget", "install", "ffmpeg", "--accept-package-agreements", "--accept-source-agreements"])
		elif OS == "Linux":
			if not shutil.which("mpv"):
				subprocess.run(["sudo", "apt", "install", "mpv", "-y"])
			if not shutil.which("feh"):
				subprocess.run(["sudo", "apt", "install", "feh", "-y"])
		return True
	except:
		print(f"problemas installing apps please install manually, exiting...")
		return False

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
		# how to get main url domain
		parsed_url = urlparse(url)
		# parsed_url is now:
		# ParseResult(scheme='https', netloc='proj.ydreams.global', path='/firjan/e7-habilidades/totem-01/idle.mp4', params='', query='', fragment='')
		base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
		#print(f"check_internet: {base_url}")
		
		response = requests.get(base_url, timeout=5)
		return True if response.status_code == 200 else False
	except requests.ConnectionError:
		return False

def signal_handler(sig, frame):
	if sig == 15:
		print('Received Close signal')
	else:
		print('Received signal:', sig)
	global running
	
	# Kill all potential media player processes
	killProcess("mpv")
	killProcess("cvlc")
	if tray_icon and tray_icon.visible:
		tray_icon.stop()
	if 'ser' in locals() and ser.is_open:
		ser.close()
	running = False
	sys.exit(0)
    
def randomize_medias():
	# We shuffle the list of medias, but keep the first one (idle media) in place.
	if len(localMedias) <= 1:
		return
	media_to_shuffle = localMedias[1:]
	random.shuffle(media_to_shuffle)
	localMedias[1:] = media_to_shuffle
	print(f"Randomized media order: {localMedias}")
	
def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: 
            return
        yield start
        start += len(sub) # use start += 1 to find overlapping matches

def find_audio_devices(audioOut):
	if OS == "Windows":
		audio_list = subprocess.check_output(["mpv", "--audio-device=help"]).decode("utf-8")
		device = ""
		device_list = []
		for i in audio_list:
			device += i
			if i == "\n":
				device_list.append(device)
				device = ""
		
		for new in device_list:
			if audioOut in new:
				get_device = list(find_all(new, "'"))
				return f"--audio-device={new[get_device[0]+1:get_device[1]]}"
		
	elif OS == "Linux":
		audio_list = subprocess.Popen(["aplay", "-l"], stdout=subprocess.PIPE)

def hide_console():
	"""Hides the console window on Windows."""
	if OS == "Windows":
		try:
			whnd = ctypes.windll.kernel32.GetConsoleWindow()
			if whnd != 0:
				ctypes.windll.user32.ShowWindow(whnd, 0) # 0 = SW_HIDE
		except Exception as e:
			print(f"Error hiding console: {e}")

def open_config_file():
	"""Launches the config_editor.py GUI application."""
	editor_script = 'config_editor.py'
	if OS == "Windows":
		editor_exe_name = os.path.join(bundle_dir, "config_editor.exe")

	# Path for running from source vs. packaged
	editor_path = os.path.join(cwd, editor_script)
	editor_exe_path = os.path.join(cwd, editor_exe_name)

	print("Attempting to open config editor...")
	try:
		if os.path.exists(editor_exe_path):
			print(f"Launching editor executable: {editor_exe_path} with file {settingsFile}")
			subprocess.Popen([editor_exe_path, settingsFile])
		elif os.path.exists(editor_path):
			print(f"Launching editor script: python {editor_path} with file {settingsFile}")
			subprocess.Popen([sys.executable, editor_path, settingsFile])
		else:
			print(f"Error: Could not find '{editor_exe_name}' or '{editor_script}' in {cwd}")
	except Exception as e:
		print(f"Error opening config file: {e}")
		if OS == "Windows":
			print("Opening config file in Notepad++")
			programFiles = os.getenv("ProgramFiles", "C:\\Program Files")
			notePadProgram = os.path.join(programFiles, "Notepad++", "notepad++.exe")
			subprocess.Popen([notePadProgram, settingsFile])
				
		elif OS == "Linux":
			subprocess.Popen(["geany", settingsFile])

def on_exit(icon, item):
	print("Exiting from tray icon...")
	icon.stop()
	signal_handler(signal.SIGINT, None)

def setup_tray_icon(icon_path):
	title = f"ydPlayer v{VERSION}"
	image = Image.open(icon_path)
	menu = (
		item(f"Version: {VERSION}", None, enabled=False),
		item('Edit Settings', open_config_file), 
		item('Exit', on_exit),
	)
	tray_icon = icon("ydPlayer", image, title, menu)
	tray_icon.run()

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
	bundle_dir = sys._MEIPASS
else:
	cwd = os.path.dirname(this_file)
	bundle_dir = os.path.dirname(os.path.abspath(__file__))

print("Current working directory:", cwd)
OS = platform.system()
print(f"Operating System: {OS}")
if OS == "Windows":
	killProcess("mpv.exe")
if OS == "Linux":
	killProcess("mpv")

# --- Setup System Tray Icon ---
tray_icon = None
icon_path = os.path.join(bundle_dir, 'icon.png')
if os.path.exists(icon_path):
	print("Starting system tray icon...")
	tray_thread = threading.Thread(target=setup_tray_icon, args=(icon_path,), daemon=True)
	tray_thread.start()
	# A small delay to allow the icon to initialize, especially on slower systems
	time.sleep(1)
else:
	print(f"Warning: Icon file not found at '{icon_path}'. System tray icon will not be displayed.")
	print("Please create an 'icon.png' file in the application directory.")


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
uart = config.get("uart", "auto")
baudrate = int(config.get("baudrate", 9600))
useSerial = bool(config.get("useSerial", False))
usbName = config.get("usbName", "CH340")
arduinoDriver = config.get("arduinoDriver", "USB\\VID_1A86&PID_7523")
if OS == "Linux":
	NEW_APP = config.get("updateApp", "https://proj.ydreams.global/ydreams/apps/ydPlayer")
elif OS == "Windows":
	NEW_APP = config.get("updateApp", "https://proj.ydreams.global/ydreams/apps/ydPlayer.exe")
medias = config.get("medias", [])

if check_internet(NEW_APP):
	check_update(NEW_APP)
	downloadContents()
else:
	for media in medias:
		mediaurl = media.get("fileUrl", "")
		fileName = os.path.basename(mediaurl)
		filePath = os.path.join(mediaFolder, fileName)
		localMedias.append(filePath)

# setup Seiral
uartOn = False
if useSerial:
	noSerial = True
	while noSerial:
		try:
			if uart == "auto":
				ports = list(serial.tools.list_ports.comports())
				hasCom = False
				for p in ports:
					if usbName in p.description:
						uart = p.device
						hasCom = True
						break
				if not hasCom:
					noSerial = False
			print(f"Using port: {uart}")
			
			ser = serial.Serial(
				port=uart,
				baudrate=baudrate,
				timeout=1
			)
			noSerial = False
			uartOn = True
			ser.flush()
		except serial.SerialException as e:
			#print("An exception occurred:", e)
			if OS == "Windows":
				if "PermissionError" in str(e):
					print("PermissionError")
					print("Restart arduino driver")
					print(f"Using driver: {arduinoDriver}")
					devconFile = os.path.join(bundle_dir, "devcon.exe")
					subprocess.run([devconFile, "disable", arduinoDriver])
					subprocess.run([devconFile, "enable", arduinoDriver])
				else:
					print("An unexpected serial error occurred.")
			else:
				print("An unexpected serial error occurred.")
		except Exception as error:
			print("An unexpected error occurred:", error)

#check number of files
if len(localMedias) == 0:
	try:
		user_input = inputimeout(prompt='No media files found, exiting...', timeout=60)
		print(f'You entered: {user_input}')
	except TimeoutOccurred:
		print('Time is up! Continuing with the script...')
	sys.exit(0)

running = True

#Check if File Exists and remove item if none exists
localMediasCopy = localMedias.copy()
localMedias = list()
for filePath in localMediasCopy:
	if os.path.isfile(filePath):
		localMedias.append(filePath)

#Play background image
if OS == "Linux":
	backGroundFile = getBackground()
	if backGroundFile:
		print(f"Background file: {backGroundFile}")
		#feh --hide-pointer -x -q -B black -g 1280x800 /home/pi/image.jpg
		backGroundPlayer = ["feh", "-Y", "-F"]
		backGroundPlayer.append(backGroundFile)
		print(f"Media Player Command: {backGroundPlayer}")
		subprocess.Popen(backGroundPlayer, stdout = subprocess.DEVNULL)


playAllAtOnce = config.get("playAllAtOnce", False)
#Create players Processes
if len(localMedias) == 1:
	playerIdle = medias[0].get("mediaPlayer", "mpv").split()
	if medias[0].get("audioOut", "auto") != "auto":
		playerIdle.append(find_audio_devices(medias[0].get("audioOut", "auto")))
	playerIdle.append("--loop")
	playerIdle.append(localMedias[0]) # Play first media as idle
	print(f"Media Player Command: {playerIdle}")
	player = subprocess.Popen(playerIdle, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	# Hide console after starting the player
	hide_console()
elif playAllAtOnce:
	multiPlayers = list()
	players = list()
	for i, media in enumerate(localMedias):
		player = medias[i].get("mediaPlayer", "mpv").split()
		if medias[i].get("audioOut", "auto") != "auto":
			player.append(find_audio_devices(medias[i].get("audioOut", "auto")))
		player.append("--loop")
		player.append(media)
		players.append(player)
		print(player)
		multiPlayers.append(subprocess.Popen(player, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
		time.sleep(0.5) # Small delay to prevent overload
	# Hide console after starting the players
	hide_console()
else:
	print(f"localMedias: {localMedias}")
	if (len(localMedias) > 0) and (uartOn):
		playerIdle = medias[0].get("mediaPlayer", "mpv").split()
		if medias[0].get("audioOut", "auto") != "auto":
			playerIdle.append(find_audio_devices(medias[0].get("audioOut", "auto")))
		playerIdle.append("--loop")
		playerIdle.append(localMedias[0]) # Play first media as idle
		print(f"Media Player Command: {playerIdle}")
		player = subprocess.Popen(playerIdle, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		# Hide console after starting the player
		hide_console()

playRandom = config.get("playRandom", False)
if playRandom and len(localMedias) > 1:
	randomize_medias()
	random_counter = 0
	num_medias = len(localMedias) - 1

print("Ready")
try:
	while running:
		if len(localMedias) == 1:
			if player.poll() is not None: # If player has terminated
				player = subprocess.Popen(playerIdle, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			time.sleep(1)
		elif uartOn:
			x=ser.readline().strip().decode()
			try:
				if player.poll() is not None:
					player = subprocess.Popen(playerIdle, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			except:
				pass
			if x.isnumeric():
				if playRandom:
					random_counter += 1
					xInt = random_counter
					if random_counter >= num_medias:
						random_counter = 0
						randomize_medias()
				else:
					xInt = int(x)
				newPlayer = medias[xInt+1].get("mediaPlayer", "mpv").split()
				if medias[xInt+1].get("audioOut", "auto") != "auto":
					newPlayer.append(find_audio_devices(medias[xInt+1].get("audioOut", "auto")))
				killProcess(newPlayer[0])
				newPlayer.append(localMedias[xInt+1])
				#print(f"Serial {xInt} : {localMedias[xInt]}")
				player = subprocess.Popen(newPlayer, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		else:
			for i, media in enumerate(localMedias):
				if playAllAtOnce:
					if multiPlayers[i].poll() is not None:
						print(players[i])
						multiPlayers[i] = subprocess.Popen(players[i], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
				else:
					player_cmd = medias[i].get("mediaPlayer", "mpv").split()
					if medias[i].get("audioOut", "auto") != "auto":
						player_cmd.append(find_audio_devices(medias[i].get("audioOut", "auto")))
					player_cmd.append(media)
					print(player_cmd)
					player_process = subprocess.Popen(player_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
					while player_process.poll() is None and running:
						time.sleep(0.5) # Wait for player to finish or for exit signal
			# Hide console after the first loop for non-serial, non-playAllAtOnce mode
			hide_console()
			if playRandom:
				randomize_medias()
		time.sleep(0.1) # Small sleep to prevent high CPU usage if not in a blocking call
			
except KeyboardInterrupt:
	print("\nExiting on user request.")
	if 'ser' in locals() and ser.is_open:
		ser.close()
	if tray_icon and tray_icon.visible:
		tray_icon.stop()
	# Kill all potential media player processes
	killProcess("mpv")
	killProcess("cvlc")
	sys.exit(0)
