import os
import sys
import configparser
import threading
from tkinter import Tk, Label, Entry, Button, filedialog, END
from flask import Flask, render_template, send_file
from tkinter.scrolledtext import ScrolledText
import time

# Initialize Flask app
app = Flask(__name__)

# Initialize ConfigParser
config = configparser.ConfigParser()

# Path to the config file
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_dir, 'config.ini')

config.read(config_path)

# Read initial values from the config file
files_dir = config['server']['directory']
extensions = [ext.strip() for ext in config['server']['extensions'].split(',')]
host = config['server']['host']

# Function to find files with the specified extensions
def find_files(directory, extensions):
    file_list = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.split('.')[-1].lower() in extensions:
                full_path = os.path.join(root, file)
                file_list.append(full_path)
    return file_list

# Flask routes
@app.route('/')
def index():
    files = find_files(files_dir, extensions)
    filenames = [os.path.basename(f) for f in files]
    return render_template('index.html', filenames=filenames)

@app.route('/<filename>')
def serve_file(filename):
    for root, _, files in os.walk(files_dir):
        if filename in files:
            return send_file(os.path.join(root, filename))
    return "File not found", 404

# Redirect stdout and stderr to Tkinter log window
class TextRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(END, message)
        self.text_widget.see(END)  # Automatically scroll to the end of the log

    def flush(self):
        pass  # Needed for compatibility with file-like objects

# Start Flask server in a separate thread
def run_server():
    app.run(host=host, port=80, debug=False)  # Disable debug mode for multithreading

# GUI Logic
class ConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("UT2K4 Redirect Server GUI")

        # Directory selection
        Label(root, text="Directory:").grid(row=0, column=0)
        self.dir_entry = Entry(root, width=50)
        self.dir_entry.grid(row=0, column=1)
        self.dir_entry.insert(END, files_dir)
        Button(root, text="Browse", command=self.select_directory).grid(row=0, column=2)

        # Host entry
        Label(root, text="Host:").grid(row=1, column=0)
        self.host_entry = Entry(root, width=50)
        self.host_entry.grid(row=1, column=1)
        self.host_entry.insert(END, host)

        # Extensions entry
        Label(root, text="Extensions:").grid(row=2, column=0)
        self.ext_entry = Entry(root, width=50)
        self.ext_entry.grid(row=2, column=1)
        self.ext_entry.insert(END, ", ".join(extensions))

        # Save button
        Button(root, text="Save Config", command=self.save_config).grid(row=3, column=1)

        # Start server button
        Button(root, text="Start Server", command=self.start_server).grid(row=4, column=1)

        # Log display
        self.log_text = ScrolledText(root, width=80, height=20)
        self.log_text.grid(row=5, column=0, columnspan=3)

        # Redirect stdout and stderr to log window
        sys.stdout = TextRedirector(self.log_text)
        sys.stderr = TextRedirector(self.log_text)

    def select_directory(self):
        dir_selected = filedialog.askdirectory()
        if dir_selected:
            self.dir_entry.delete(0, END)
            self.dir_entry.insert(END, dir_selected)

    def save_config(self):
        config['server']['directory'] = self.dir_entry.get()
        config['server']['host'] = self.host_entry.get()
        config['server']['extensions'] = self.ext_entry.get()

        with open(config_path, 'w') as configfile:
            config.write(configfile)

        self.log("Config saved!")

    def start_server(self):
        # Save config before starting the server
        self.save_config()
        self.log("Starting server...")

        # Start Flask server in a separate thread
        threading.Thread(target=run_server, daemon=True).start()

    def log(self, message):
        print(message)

# Main loop
if __name__ == '__main__':
    root = Tk()
    gui = ConfigGUI(root)
    root.mainloop()
