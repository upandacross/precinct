#!/usr/bin/env python3
"""
WSGI entry point for the Precinct Leaders application.
This file provides the WSGI application object for production deployment.
"""

from main import create_app

# Create the application instance
application = create_app()

if __name__ == "__main__":
    # For development/testing, run with Waitress
    from waitress import serve
    print("Starting Waitress WSGI server on http://0.0.0.0:8080")
    serve(application, host='0.0.0.0', port=8080)