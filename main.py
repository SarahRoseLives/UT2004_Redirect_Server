import os
import sys
import configparser
from flask import Flask, render_template, send_file

app = Flask(__name__)

# Get the directory where the executable or script is located
if getattr(sys, 'frozen', False):
    # If the app is frozen (packaged by PyInstaller)
    base_dir = os.path.dirname(sys.executable)
else:
    # If running normally
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Path to the config file
config_path = os.path.join(base_dir, 'config.ini')

config = configparser.ConfigParser()
config.read(config_path)


# Directory where files are located
files_dir = config['server']['directory']

# List of file extensions to filter by, stripping extra spaces
extensions = [ext.strip() for ext in config['server']['extensions'].split(',')]

# Host address to bind to
host = config['server']['host']

# Function to find files with the specified extensions
def find_files(directory, extensions):
    file_list = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.split('.')[-1].lower() in extensions:  # Match case-insensitively
                full_path = os.path.join(root, file)
                file_list.append(full_path)  # Store full paths for serving files
    return file_list

# Index route
@app.route('/')
def index():
    files = find_files(files_dir, extensions)
    filenames = [os.path.basename(f) for f in files]  # Strip directory paths for displaying
    return render_template('index.html', filenames=filenames)

# Route to serve files directly from their subdirectories as web root
@app.route('/<filename>')
def serve_file(filename):
    # Find the file in the directory tree
    for root, _, files in os.walk(files_dir):
        if filename in files:
            return send_file(os.path.join(root, filename))
    return "File not found", 404

if __name__ == '__main__':
    app.run(host=host, port=80, debug=True)
