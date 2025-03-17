import os

HURLSTOR_URL = 'http://hurlstor.soest.hawaii.edu'


class Config:
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = 'flask_session'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    LOCAL_APP_URL = 'http://127.0.0.1:8000'
    TATOR_URL = 'https://cloud.tator.io'
    VARS_ANNOTATION_URL = f'{HURLSTOR_URL}:8082/v1/annotations'
    VARS_CONCEPT_LIST_URL = f'{HURLSTOR_URL}:8083/v1/concept'
    VARS_PHYLOGENY_URL = f'{HURLSTOR_URL}:8083/v1/phylogeny/up'
    VARS_SEQUENCE_LIST_URL = f'{HURLSTOR_URL}:8084/v1/videosequences/names'
    VARS_DIVE_QUERY_URL = f'{HURLSTOR_URL}:8086/query/dive'

    DARC_REVIEW_HEADERS = {'API-Key': os.environ.get('DARC_REVIEW_API_KEY')}
    SECRET_KEY = os.environ.get('APP_SECRET_KEY')

    if os.environ.get('_FLASK_ENV') == 'no_server_edits':
        print('\n\nLOCAL DEVELOPMENT MODE: No server edits\n\n')
        ANNOSAURUS_URL = ''
        ANNOSAURUS_CLIENT_SECRET = ''
        DARC_REVIEW_URL = 'http://127.0.0.1:5000'
    else:
        ANNOSAURUS_URL = f'{HURLSTOR_URL}:8082/v1'
        ANNOSAURUS_CLIENT_SECRET = os.environ.get('ANNOSAURUS_CLIENT_SECRET')
        DARC_REVIEW_URL = 'https://hurlstor.soest.hawaii.edu:5000'
