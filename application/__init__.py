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
from application.blueprints.tator import tator_bp
from application.blueprints.vars import vars_bp
from application.blueprints.image_review import image_review_bp
from application.blueprints.image_review.tator import tator_image_review_bp
from application.blueprints.image_review.vars import vars_image_review_bp
from application.blueprints.image_review.external_review import external_review_bp
from application.blueprints.qaqc import qaqc_bp
from application.blueprints.qaqc.tator import tator_qaqc_bp
from application.blueprints.qaqc.vars import vars_qaqc_bp

app.register_blueprint(tator_bp)
app.register_blueprint(vars_bp)
app.register_blueprint(image_review_bp)
app.register_blueprint(tator_image_review_bp)
app.register_blueprint(vars_image_review_bp)
app.register_blueprint(external_review_bp)
app.register_blueprint(qaqc_bp)
app.register_blueprint(tator_qaqc_bp)
app.register_blueprint(vars_qaqc_bp)

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
