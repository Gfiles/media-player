#!/usr/bin/env python3
"""
Audio Device Selector GUI Application

A Python GUI application that allows users to:
1. Select audio output devices
2. Select audio channels (stereo/mono)
3. Select and play audio files

sudo apt-get install portaudio19-dev python3-pyaudio
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pyaudio
import wave
import threading
import os
import json

class AudioDeviceSelector:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Device Selector")
        self.root.geometry("600x500")
        
        # Audio settings
        self.audio = pyaudio.PyAudio()
        self.current_device = None
        self.current_channels = 2
        self.audio_file = None
        self.is_playing = False
        self.stream = None
        self.wf = None
        
        # Create GUI
        self.create_widgets()
        self.load_audio_devices()
        
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Device selection
        device_frame = ttk.LabelFrame(main_frame, text="Audio Device Selection", padding="10")
        device_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(device_frame, text="Select Audio Device:").grid(row=0, column=0, sticky=tk.W)
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(device_frame, textvariable=self.device_var, width=50)
        self.device_combo.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E))
        self.device_combo.bind('<<ComboboxSelected>>', self.on_device_selected)
        
        # Channel selection
        channel_frame = ttk.LabelFrame(main_frame, text="Channel Configuration", padding="10")
        channel_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.channel_var = tk.IntVar(value=2)
        ttk.Radiobutton(channel_frame, text="Stereo (2 channels)", variable=self.channel_var, value=2).grid(row=0, column=0, padx=(0, 20))
        ttk.Radiobutton(channel_frame, text="Mono (1 channel)", variable=self.channel_var, value=1).grid(row=0, column=1)
        
        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="Audio File Selection", padding="10")
        file_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(file_frame, text="Selected File:").grid(row=0, column=0, sticky=tk.W)
        self.file_label = ttk.Label(file_frame, text="No file selected", relief=tk.SUNKEN)
        self.file_label.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E))
        
        ttk.Button(file_frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=(10, 0))
        
        # Playback controls
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        self.play_button = ttk.Button(control_frame, text="Play", command=self.play_audio, state=tk.DISABLED)
        self.play_button.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_audio, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=(0, 5))
        
        self.pause_button = ttk.Button(control_frame, text="Pause", command=self.pause_audio, state=tk.DISABLED)
        self.pause_button.grid(row=0, column=2)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_label.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
    def load_audio_devices(self):
        """Load available audio devices"""
        devices = []
        info = self.audio.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        for i in range(num_devices):
            device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
            if device_info.get('maxOutputChannels') > 0:
                devices.append({
                    'index': i,
                    'name': device_info.get('name'),
                    'channels': device_info.get('maxOutputChannels')
                })
        
        self.device_combo['values'] = [f"{d['index']}: {d['name']} ({d['channels']} channels)" for d in devices]
        if devices:
            self.device_combo.current(0)
            self.current_device = devices[0]
    
    def on_device_selected(self, event):
        """Handle device selection change"""
        selection = self.device_var.get()
        if selection:
            device_index = int(selection.split(':')[0])
            device_info = self.audio.get_device_info_by_index(device_index)
            self.current_device = {
                'index': device_index,
                'name': device_info['name'],
                'channels': device_info['maxOutputChannels']
            }
            self.update_status(f"Selected device: {self.current_device['name']}")
    
    def browse_file(self):
        """Browse for audio file"""
        filetypes = [
            ("Audio files", "*.wav *.mp3 *.ogg *.flac"),
            ("WAV files", "*.wav"),
            ("MP3 files", "*.mp3"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=filetypes
        )
        
        if filename:
            self.audio_file = filename
            self.file_label.config(text=os.path.basename(filename))
            self.play_button.config(state=tk.NORMAL)
            self.update_status(f"Selected file: {os.path.basename(filename)}")
    
    def play_audio(self):
        """Play the selected audio file"""
        if not self.audio_file or not self.current_device:
            messagebox.showwarning("Warning", "Please select both audio device and file")
            return
        
        try:
            self.wf = wave.open(self.audio_file, 'rb')
            self.is_playing = True
            
            # Update UI
            self.play_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.NORMAL)
            self.progress.start()
            
            # Start playback in separate thread
            self.play_thread = threading.Thread(target=self._play_audio_thread)
            self.play_thread.daemon = True
            self.play_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error playing audio: {str(e)}")
            self.reset_ui()
    
    def _play_audio_thread(self):
        """Audio playback thread"""
        try:
            # Open stream
            self.stream = self.audio.open(
                format=self.audio.get_format_from_width(self.wf.getsampwidth()),
                channels=self.channel_var.get(),
                rate=self.wf.getframerate(),
                output=True,
                output_device_index=self.current_device['index']
            )
            
            # Read and play audio
            chunk = 1024
            data = self.wf.readframes(chunk)
            
            while data and self.is_playing:
                self.stream.write(data)
                data = self.wf.readframes(chunk)
            
            # Clean up
            self.stop_audio()
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Playback error: {str(e)}"))
            self.root.after(0, self.reset_ui)
    
    def stop_audio(self):
        """Stop audio playback"""
        self.is_playing = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        if self.wf:
            self.wf.close()
            self.wf = None
        
        self.reset_ui()
    
    def pause_audio(self):
        """Pause/resume audio playback"""
        if self.stream:
            if self.stream.is_active():
                self.stream.stop_stream()
                self.pause_button.config(text="Resume")
            else:
                self.stream.start_stream()
                self.pause_button.config(text="Pause")
    
    def reset_ui(self):
        """Reset UI to initial state"""
        self.progress.stop()
        self.play_button.config(state=tk.NORMAL if self.audio_file else tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.DISABLED, text="Pause")
        self.update_status("Ready")
    
    def update_status(self, message):
        """Update status label"""
        self.status_label.config(text=message)
    
    def on_closing(self):
        """Clean up on application close"""
        self.stop_audio()
        self.audio.terminate()
        self.root.destroy()

def main():
    """Main function"""
    root = tk.Tk()
    app = AudioDeviceSelector(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
