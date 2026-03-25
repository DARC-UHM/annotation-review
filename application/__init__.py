import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_session import Session
from time import time


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY')
    app.config.from_object('application.config.Config')

    Session(app)

    from application.main import main_bp, page_not_found, server_error
    from application.image_reference import image_reference_bp
    from application.image_review import image_review_bp
    from application.qaqc import qaqc_bp
    from application.vars import vars_bp
    from application.tator import tator_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(image_reference_bp, url_prefix='/image-reference')
    app.register_blueprint(image_review_bp, url_prefix='/image-review')
    app.register_blueprint(qaqc_bp, url_prefix='/qaqc')
    app.register_blueprint(vars_bp, url_prefix='/vars')
    app.register_blueprint(tator_bp, url_prefix='/tator')

    app.register_error_handler(404, page_not_found)
    app.register_error_handler(Exception, server_error)

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

    return app
