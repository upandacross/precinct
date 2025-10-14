#!/usr/bin/env python3
"""
Script to run Flask app with proper logging to capture all output.
"""
import sys
import os
from datetime import datetime

# Redirect stdout and stderr to log file
log_file = os.path.join(os.path.dirname(__file__), 'flask.log')

class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'a')
        
    def write(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_msg = f"[{timestamp}] {message}"
        self.terminal.write(formatted_msg)
        self.log.write(formatted_msg)
        self.log.flush()
        
    def flush(self):
        self.terminal.flush()
        self.log.flush()

class ErrorLogger:
    def __init__(self, filename):
        self.terminal = sys.stderr
        self.log = open(filename, 'a')
        
    def write(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_msg = f"[{timestamp}] ERROR: {message}"
        self.terminal.write(formatted_msg)
        self.log.write(formatted_msg)
        self.log.flush()
        
    def flush(self):
        self.terminal.flush()
        self.log.flush()

# Clear previous log
with open(log_file, 'w') as f:
    f.write(f"=== Flask App Log Started at {datetime.now()} ===\n")

# Set up logging
sys.stdout = Logger(log_file)
sys.stderr = ErrorLogger(log_file)

print("Starting Flask application with logging...")

try:
    from main import create_app
    print("Successfully imported create_app")
    
    app = create_app()
    print("Successfully created Flask app")
    
    print("Starting Flask server on 0.0.0.0:5000...")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()