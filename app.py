from flask import Flask
import os
import config

app = Flask(__name__)

@app.route('/')
def index():

    return "Hello, World from flask app.py!"
