import os
import webbrowser
import atexit

from dotenv import load_dotenv
from flask import Flask, session
from flask_session import Session
from threading import Timer


def open_browser():
    if os.environ.get('_FLASK_ENV') == 'production':
        webbrowser.open_new('http://127.0.0.1:8000')
    print('\n\033[1;32;48mApplication running. Press CTRL + C to stop.\033[1;37;0m\n')


def clear_temp_session_vals():
    session.pop('reviewers', None)
    session.pop('vars_video_sequences', None)
    session.pop('vars_concepts', None)


load_dotenv()
atexit.register(clear_temp_session_vals)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.config.from_object('application.config.Config')

Session(app)

print('\nLaunching application...')
Timer(1, open_browser).start()

from application import routes
