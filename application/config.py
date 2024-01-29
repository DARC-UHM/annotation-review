import os


class Config:
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = 'flask_session'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    HURLSTOR_URL = 'http://hurlstor.soest.hawaii.edu'
    LOCAL_APP_URL = 'http://127.0.0.1:8000'
    TATOR_URL = 'https://cloud.tator.io'

    DARC_REVIEW_HEADERS = {'API-Key': os.environ.get('DARC_REVIEW_API_KEY')}
    SECRET_KEY = os.environ.get('APP_SECRET_KEY')

    if os.environ.get('_FLASK_ENV') == 'no_server_edits':
        print('\n\nLOCAL DEVELOPMENT MODE: No server edits\n\n')
        ANNOSAURUS_URL = ''
        ANNOSAURUS_CLIENT_SECRET = ''
        DARC_REVIEW_URL = 'http://127.0.0.1:5000'
    else:
        ANNOSAURUS_URL = os.environ.get('ANNOSAURUS_URL')
        ANNOSAURUS_CLIENT_SECRET = os.environ.get('ANNOSAURUS_CLIENT_SECRET')
        DARC_REVIEW_URL = 'https://hurlstor.soest.hawaii.edu:5000'
