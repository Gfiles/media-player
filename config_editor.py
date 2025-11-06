# pyinstaller --onefile --clean --icon=icon.png config_editor.py
import platform
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import serial.tools.list_ports
import subprocess
import argparse

OS = platform.system()
machine_arch = platform.machine().lower()
if OS == "Linux":
    if machine_arch in ('aarch64', 'arm64'):
        OS = "Rasp-Pi"
print(f"OS: {OS}")

class JsonEditorApp:
    def __init__(self, root, file_to_load=None):
        self.root = root
        self.root.title("ydPlayer JSON Config Editor")
        self.root.geometry("800x600")

        self.file_path = tk.StringVar()
        self.config_data = {}
        self.media_widgets = []

        # --- Main Frames ---
        top_frame = ttk.Frame(root, padding="10")
        top_frame.pack(fill=tk.X)

        self.notebook = ttk.Notebook(root, padding="10")
        self.notebook.pack(expand=True, fill="both")

        # --- Help/Info Box ---
        info_frame = ttk.LabelFrame(root, text="Information", padding="10")
        info_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 10))

        self.info_text = tk.Text(info_frame, height=4, wrap="word", state="disabled", background=root.cget('bg'), relief=tk.FLAT)
        self.info_text.pack(fill=tk.X, expand=True)

        self.general_tab = ttk.Frame(self.notebook)
        self.serial_tab = ttk.Frame(self.notebook)
        self.media_tab = ttk.Frame(self.notebook)

        self.help_texts = {
            "updateApp": "The URL to the application executable for automatic updates. The application will check this link on startup.",
            "playAllAtOnce": "If checked, all media files in the list will be played simultaneously, each in its own player instance.",
            "playRandom": "If checked, the media files (except the first one, which is the idle video) will be played in a random order when triggered.",
            "useSerial": "Enable or disable serial communication (e.g., for Arduino or button input). This enables the fields below.",
            "uart": "The COM port for the serial device. 'auto' will attempt to find the device specified in 'usbName'.",
            "baudrate": "The communication speed for the serial port (bits per second). Must match the device's setting.",
            "usbName": "A unique part of the serial device's name used for auto-detection when 'uart' is set to 'auto'.",
            "arduinoDriver": "The hardware ID of the Arduino driver, used on Windows to automatically restart the driver if a permission error occurs."
        }

        self.notebook.add(self.general_tab, text='General')
        self.notebook.add(self.media_tab, text='Media List')

        # --- Top Frame: File Operations ---
        ttk.Button(top_frame, text="Load Config", command=self.load_file).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(top_frame, text="Save Config", command=self.save_file).pack(side=tk.LEFT)
        ttk.Label(top_frame, text="File:").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Entry(top_frame, textvariable=self.file_path, state="readonly").pack(side=tk.LEFT, expand=True, fill=tk.X)

        # --- General Settings Tab ---
        self.general_widgets = {}
        if OS == "Windows":
            general_fields = ["updateApp", "playAllAtOnce", "playRandom", "useSerial", "uart", "baudrate", "usbName", "arduinoDriver"]
        else:
            general_fields = ["updateApp", "playAllAtOnce", "playRandom", "useSerial", "uart", "baudrate", "usbName"]
        for i, field in enumerate(general_fields):
            ttk.Label(self.general_tab, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky="w")
            
            # Create a frame for widgets that might have a button next to them
            widget_frame = ttk.Frame(self.general_tab)
            widget_frame.grid(row=i, column=1, padx=5, pady=5, sticky="ew")

            if field == "useSerial":
                var = tk.BooleanVar()
                widget = ttk.Checkbutton(widget_frame, variable=var, command=self.toggle_serial_widgets)
            elif field == "playAllAtOnce":
                var = tk.BooleanVar()
                widget = ttk.Checkbutton(widget_frame, variable=var)
            elif field == "playRandom":
                var = tk.BooleanVar()
                widget = ttk.Checkbutton(widget_frame, variable=var)
            elif field == "uart":
                var = tk.StringVar()
                widget = ttk.Combobox(widget_frame, textvariable=var, width=10)
                self.populate_com_ports(widget)
                refresh_btn = ttk.Button(widget_frame, text="Refresh", command=lambda w=widget: self.populate_com_ports(w))
                refresh_btn.grid(row=0, column=1, padx=(5, 0))
            elif field == "baudrate":
                var = tk.IntVar()
                widget = ttk.Combobox(widget_frame, textvariable=var, width=10)
                widget['values'] = [300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 57600, 115200]
                widget.set(9600) # Set a default value
            else:
                var = tk.StringVar()
                widget = ttk.Entry(widget_frame, textvariable=var, width=60)

            widget.grid(row=0, column=0, sticky="w")
            self.general_widgets[field] = (widget, var)

            # Bind hover events for showing help text
            widget.bind("<Enter>", lambda event, f=field: self.on_widget_enter(event, f))
            widget.bind("<Leave>", self.on_widget_leave)

        self.general_tab.columnconfigure(1, weight=1)


        # --- Media List Tab ---
        media_controls_frame = ttk.Frame(self.media_tab)
        media_controls_frame.pack(fill=tk.X, pady=5)
        ttk.Button(media_controls_frame, text="Add Media", command=self.add_media_item).pack(side=tk.LEFT)
        ttk.Button(media_controls_frame, text="Remove Selected", command=self.remove_media_item).pack(side=tk.LEFT, padx=5)

        cols = ("mediaPlayer", "audioOut", "fileUrl")
        self.media_tree = ttk.Treeview(self.media_tab, columns=cols, show='headings', selectmode='browse')
        for col in cols:
            self.media_tree.heading(col, text=col.capitalize())
            if col == "audioOut":
                self.media_tree.column(col, width=100, stretch=tk.NO) # Make this column smaller and fixed width
            elif col == "fileUrl":
                self.media_tree.column(col, width=350)
            else:
                self.media_tree.column(col, width=250)
        self.media_tree.pack(expand=True, fill="both")
        self.media_tree.bind("<Double-1>", self.edit_media_item)
        
        # Bind hover events for the media list itself
        self.media_tree.bind("<Enter>", self.on_media_list_enter)
        self.media_tree.bind("<Leave>", self.on_widget_leave) # Re-use the leave handler

        # --- Auto-load default file ---
        if file_to_load and os.path.exists(file_to_load):
            self.file_path.set(os.path.abspath(file_to_load))
            self.load_data()
        else:
            self.auto_load_default()

    def on_widget_enter(self, event, field_name):
        """Display help text when the mouse enters a widget."""
        info = self.help_texts.get(field_name, "No information available for this setting.")
        self.info_text.config(state="normal")
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", info)
        self.info_text.config(state="disabled")

    def on_widget_leave(self, event):
        """Clear the help text when the mouse leaves a widget."""
        self.info_text.config(state="normal")
        self.info_text.delete("1.0", tk.END)
        self.info_text.config(state="disabled")

    def on_media_list_enter(self, event):
        """Display help text for the media list Treeview."""
        info = "This is the list of media files. Double-click any item to open the editor for that item."
        self.info_text.config(state="normal")
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", info)
        self.info_text.config(state="disabled")

    def populate_com_ports(self, combobox_widget):
        """Fetches available COM ports and populates the combobox."""
        try:
            ports = serial.tools.list_ports.comports()
            port_list = [port.device for port in ports]
            port_list.insert(0, "auto") # Add 'auto' as the first option
            combobox_widget['values'] = port_list
        except Exception as e:
            messagebox.showerror("Error", f"Could not fetch COM ports: {e}")

    def auto_load_default(self):
        """Automatically load ydPlayer.json if it exists in the current directory."""
        default_file = "ydPlayer.json"
        if os.path.exists(default_file):
            self.file_path.set(os.path.abspath(default_file))
            self.load_data()

    def load_file(self):
        """Open a file dialog to select a JSON file."""
        path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Select Configuration File"
        )
        if path:
            self.file_path.set(path)
            self.load_data()

    def load_data(self):
        """Load data from the selected JSON file and populate the GUI."""
        path = self.file_path.get()
        if not path:
            return
        try:
            with open(path, 'r') as f:
                self.config_data = json.load(f)
            
            # Populate General tab
            for field, (widget, var) in self.general_widgets.items():
                value = self.config_data.get(field)
                if value is not None:
                    var.set(value)

            self.toggle_serial_widgets() # Set initial state of serial widgets

            # Populate Media Tree
            self.media_tree.delete(*self.media_tree.get_children())
            for item in self.config_data.get("medias", []):
                self.media_tree.insert("", "end", values=(
                    item.get("mediaPlayer", ""),
                    item.get("audioOut", ""),
                    item.get("fileUrl", "")
                ))
            messagebox.showinfo("Success", "Configuration loaded successfully.")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")
            self.config_data = {}

    def save_file(self):
        """Save the current GUI state back to the JSON file."""
        path = self.file_path.get()
        if not path:
            messagebox.showwarning("Warning", "No file loaded. Please load a file first.")
            return

        # Update config_data from GUI
        # General Tab
        for field, (widget, var) in self.general_widgets.items():
            self.config_data[field] = var.get()

        # Media List
        media_list = []
        for iid in self.media_tree.get_children():
            values = self.media_tree.item(iid, 'values')
            media_list.append({
                "mediaPlayer": values[0],
                "audioOut": values[1],
                "fileUrl": values[2],
                "lastModified": "" # Preserve this field
            })
        self.config_data["medias"] = media_list

        try:
            with open(path, 'w') as f:
                json.dump(self.config_data, f, indent=4)
            messagebox.showinfo("Success", "Configuration saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

    def add_media_item(self):
        """Add a new blank item to the media list."""
        new_item_values = ("mpv.exe -fs --volume=100 --osc=no --title=mpvPlay", "auto", "")
        self.media_tree.insert("", "end", values=new_item_values)
        self.edit_media_item(event=None, new_item=True)

    def remove_media_item(self):
        """Remove the selected item from the media list."""
        selected_item = self.media_tree.selection()
        if selected_item:
            self.media_tree.delete(selected_item)

    def edit_media_item(self, event, new_item=False):
        """Open a dialog to edit the selected media item."""
        if not new_item:
            selected_item_id = self.media_tree.selection()
            if not selected_item_id:
                return
            selected_item_id = selected_item_id[0]
            item_values = self.media_tree.item(selected_item_id, 'values')
        else:
            # Get the last item added
            children = self.media_tree.get_children()
            if not children: return
            selected_item_id = children[-1]
            item_values = self.media_tree.item(selected_item_id, 'values')

        # Create a Toplevel window for editing
        editor = tk.Toplevel(self.root)
        editor.title("Edit Media Item")
        editor.geometry("600x300")

        fields = ["mediaPlayer", "audioOut", "fileUrl"]
        entries = {}

        media_help_texts = {
            "mediaPlayer": "The command-line instruction to launch the media player (e.g., 'mpv.exe -fs --volume=100 --osc=no --title=mpvPlay' for Windows or 'cvlc -f --no-osd --play-and-exit -q' for Raspberry Pi). ",
            "audioOut": "The name of the audio output device. Normally used with multiple audio devices",
            "fileUrl": "The local path or web URL for the media file. Use the 'Browse...' button to select a local file."
        }

        def on_editor_widget_enter(event, field_name):
            info = media_help_texts.get(field_name, "No information available.")
            info_text.config(state="normal")
            info_text.delete("1.0", tk.END)
            info_text.insert("1.0", info)
            info_text.config(state="disabled")

        def on_editor_widget_leave(event):
            info_text.config(state="normal")
            info_text.delete("1.0", tk.END)
            info_text.config(state="disabled")


        def get_audio_devices():
            """Gets a list of audio device names from mpv."""
            devices = ["auto"] # Start with auto
            try:
                # Run mpv to get the list of audio devices
                result = subprocess.check_output(["mpv", "--audio-device=help"], text=True, stderr=subprocess.PIPE)
                for line in result.splitlines():
                    if "' (" in line:
                        # Extract the description part, e.g., "Description: Speakers (Realtek Audio)"
                        device_name = line.split("' ", 1)[1].strip()
                        devices.append(device_name)
            except (FileNotFoundError, subprocess.CalledProcessError) as e:
                print(f"Could not get audio devices from mpv: {e}")
            return devices

        def browse_media_file(entry_var):
            """Opens a file dialog to select a media file."""
            filetypes = [
                ("Media Files", "*.mp4 *.mkv *.avi *.mov *.mp3 *.wav *.flac *.ogg"),
                ("Video Files", "*.mp4 *.mkv *.avi *.mov"),
                ("Audio Files", "*.mp3 *.wav *.flac *.ogg"),
                ("All files", "*.*")
            ]
            filename = filedialog.askopenfilename(
                title="Select Media File",
                filetypes=filetypes
            )
            if filename:
                entry_var.set(filename)

        for i, field in enumerate(fields):
            ttk.Label(editor, text=f"{field.capitalize()}:").grid(row=i, column=0, padx=10, pady=10, sticky="w")
            var = tk.StringVar(value=item_values[i])
            
            widget_frame = ttk.Frame(editor)
            widget_frame.grid(row=i, column=1, padx=10, pady=5, sticky="ew")

            if field == "audioOut":
                widget = ttk.Combobox(widget_frame, textvariable=var)
                widget['values'] = get_audio_devices()
            elif field == "fileUrl":
                widget = ttk.Entry(widget_frame, textvariable=var)
                ttk.Button(widget_frame, text="Browse...", command=lambda v=var: browse_media_file(v)).pack(side=tk.RIGHT, padx=(5,0))
            else:
                widget = ttk.Entry(widget_frame, textvariable=var)
            
            widget.pack(side=tk.LEFT, fill=tk.X, expand=True)
            widget.bind("<Enter>", lambda event, f=field: on_editor_widget_enter(event, f))
            widget.bind("<Leave>", on_editor_widget_leave)
            entries[field] = var

        def on_save():
            new_values = (
                entries["mediaPlayer"].get(),
                entries["audioOut"].get(),
                entries["fileUrl"].get()
            )
            self.media_tree.item(selected_item_id, values=new_values)
            editor.destroy()

        save_button = ttk.Button(editor, text="Save", command=on_save)
        save_button.grid(row=len(fields), column=0, columnspan=2, pady=10, sticky="ew", padx=10)

        # --- Help/Info Box for Editor ---
        info_frame = ttk.LabelFrame(editor, text="Information", padding="10")
        info_frame.grid(row=len(fields) + 1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        info_text = tk.Text(info_frame, height=3, wrap="word", state="disabled", background=editor.cget('bg'), relief=tk.FLAT)
        info_text.pack(fill=tk.X, expand=True)

        editor.columnconfigure(1, weight=1)
        editor.transient(self.root)
        editor.grab_set()
        self.root.wait_window(editor)


    def toggle_serial_widgets(self, *args):
        """Enable or disable serial-related widgets based on the useSerial checkbox."""
        try:
            use_serial = self.general_widgets["useSerial"][1].get()
            state = "normal" if use_serial else "disabled"

            for field in ["uart", "baudrate", "usbName", "arduinoDriver"]:
                # The widget is the first element in the tuple
                self.general_widgets[field][0].config(state=state)
        except KeyError as e:
            print(f"Warning: Widget key not found during toggle: {e}")

class MediaItemEditor(tk.Toplevel):
    def __init__(self, parent, item_data, on_save_callback):
        super().__init__(parent)
        self.title("Edit Media Item")
        self.geometry("500x200")
        self.transient(parent)
        self.grab_set()

        self.item_data = item_data
        self.on_save_callback = on_save_callback
        self.entries = {}

        fields = ["mediaPlayer", "audioOut", "fileUrl"]
        for i, field in enumerate(fields):
            ttk.Label(self, text=f"{field.capitalize()}:").grid(row=i, column=0, padx=10, pady=10, sticky="w")
            var = tk.StringVar(value=self.item_data.get(field, ""))
            entry = ttk.Entry(self, textvariable=var, width=60)
            entry.grid(row=i, column=1, padx=10, pady=10, sticky="ew")
            self.entries[field] = var

        self.columnconfigure(1, weight=1)

        save_button = ttk.Button(self, text="Save", command=self.on_save)
        save_button.grid(row=len(fields), column=0, columnspan=2, pady=10)

    def on_save(self):
        """Update item_data and call the callback."""
        for field, var in self.entries.items():
            self.item_data[field] = var.get()
        self.on_save_callback(self.item_data)
        self.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    parser = argparse.ArgumentParser(description="JSON Config Editor for ydPlayer")
    parser.add_argument("file", nargs='?', default=None, help="Path to the JSON config file to load.")
    args = parser.parse_args()

    app = JsonEditorApp(root, file_to_load=args.file)
    root.mainloop()
