import os
import webbrowser
from flask import Flask
from threading import Timer
from dotenv import load_dotenv


def open_browser():
    if os.environ.get('_FLASK_ENV') == 'production':
        webbrowser.open_new('http://127.0.0.1:8000')
    print('\n\033[1;32;48mApplication running. Press CTRL + C to stop.\033[1;37;0m\n')


load_dotenv()
app = Flask(__name__)

print('\nLaunching application...')
Timer(1, open_browser).start()

from application import routes
