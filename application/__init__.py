import os
import webbrowser
import atexit

from flask import Flask
from flask_session import Session
from threading import Timer
from dotenv import load_dotenv


def open_browser():
    if os.environ.get('_FLASK_ENV') == 'production':
        webbrowser.open_new('http://127.0.0.1:8000')
    print('\n\033[1;32;48mApplication running. Press CTRL + C to stop.\033[1;37;0m\n')


def remove_session_files():
    print('Removing session files...')
    session_folder = app.config['SESSION_FILE_DIR']
    for filename in os.listdir(session_folder):
        filepath = os.path.join(session_folder, filename)
        os.remove(filepath)


load_dotenv()

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = 'flask_session'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

Session(app)

atexit.register(remove_session_files)

print('\nLaunching application...')
Timer(1, open_browser).start()

from application import routes
