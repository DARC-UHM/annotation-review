import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_session import Session
from time import time


load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.config.from_object('application.config.Config')

Session(app)

print('\nLaunching application...')

from application import main
from application.image_review import image_review_bp
from application.qaqc import qaqc_bp
from application.vars import vars_bp
from application.tator import tator_bp

app.register_blueprint(image_review_bp, url_prefix='/image-review')
app.register_blueprint(qaqc_bp, url_prefix='/qaqc')
app.register_blueprint(vars_bp, url_prefix='/vars')
app.register_blueprint(tator_bp, url_prefix='/tator')

print('\n\033[1;32;48mApplication running. Press CTRL + C to stop.\033[1;37;0m\n')

if os.environ.get('_FLASK_ENV') == 'production':
    import webbrowser
    webbrowser.open_new('http://127.0.0.1:8000')

# clean VARS frame cache
try:
    current_time = time()
    for cache_file in Path('cache', 'vars_frames').glob('*'):
        if not cache_file.is_file():
            continue
        file_age = current_time - cache_file.stat().st_mtime
        if file_age > 60 * 60 * 24 * 14:  # remove files older than 2 weeks
            file_size = cache_file.stat().st_size
            cache_file.unlink()
except Exception as e:
    print(f'Error during cache cleanup: {str(e)}')
