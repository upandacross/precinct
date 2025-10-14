#!/usr/bin/env python3
"""
Production runner with logging for troubleshooting
"""
import sys
import os
from datetime import datetime

# Set up logging
log_file = os.path.join(os.path.dirname(__file__), 'wsgi.log')
with open(log_file, 'w') as f:
    f.write(f"=== WSGI Production Server Log Started at {datetime.now()} ===\n")

class Logger:
    def __init__(self, filename, stream):
        self.terminal = stream
        self.log = open(filename, 'a')
        
    def write(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if message.strip():  # Only log non-empty messages
            formatted_msg = f"[{timestamp}] {message}"
            self.terminal.write(formatted_msg)
            self.log.write(formatted_msg)
            self.log.flush()
        else:
            self.terminal.write(message)
            self.log.write(message)
        
    def flush(self):
        self.terminal.flush()
        self.log.flush()

# Set up logging
sys.stdout = Logger(log_file, sys.stdout)
sys.stderr = Logger(log_file, sys.stderr)

print("Starting production WSGI server...")

try:
    from main import create_app
    print("Successfully imported create_app")
    
    app = create_app()
    print("Successfully created Flask app")
    
    from waitress import serve
    print("Starting Waitress server on 0.0.0.0:8080...")
    
    # Run Waitress server
    serve(app, host='0.0.0.0', port=8080, threads=6)
    
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()