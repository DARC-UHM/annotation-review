import os

HURLSTOR_URL = 'https://hurlstor.soest.hawaii.edu'


class Config:
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = 'flask_session'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_FILE_THRESHOLD = 10
    LOCAL_APP_URL = 'http://127.0.0.1:8000'
    TATOR_URL = 'https://cloud.tator.io'
    TATOR_PROJECT_ID = 26
    VARS_ANNOSAURUS_URL = f'{HURLSTOR_URL}/anno/v1'
    VARS_KNOWLEDGE_BASE_URL = f'{HURLSTOR_URL}/kb/v1'
    VARS_VAMPIRE_SQUID_URL = f'{HURLSTOR_URL}/vam/v1'
    # VARS_CHARYBDIS_URL = f'{HURLSTOR_URL}/references/v1'
    # TODO remove this in favor of the endpoint above once we fix SSL for Charybdis
    VARS_CHARYBDIS_URL = 'http://hurlstor.soest.hawaii.edu:8086'

    DARC_REVIEW_HEADERS = {'API-Key': os.environ.get('DARC_REVIEW_API_KEY')}
    SECRET_KEY = os.environ.get('APP_SECRET_KEY')

    if os.environ.get('_FLASK_ENV') == 'no_server_edits':
        print('\n\nLOCAL DEVELOPMENT MODE: No server edits\n\n')
        ANNOSAURUS_CLIENT_SECRET = ''
        DARC_REVIEW_URL = 'http://127.0.0.1:5000'
    else:
        ANNOSAURUS_CLIENT_SECRET = os.environ.get('ANNOSAURUS_CLIENT_SECRET')
        DARC_REVIEW_URL = 'https://hurlstor.soest.hawaii.edu:5000'
        # https://hurlstor.soest.hawaii.edu:5000 == https://darc.soest.hawaii.edu
        # We set up a proxy to point darc.soest.hawaii.edu to hurlstor.soest.hawaii.edu:5000. External reviewers should
        # access their page using the darc.soest.hawaii.edu URL. This app primarily uses the hurlstor URL. This can be
        # changed in the future if needed, but prefer to continue using the hurlstor URL so it's clearer that this is
        # the actual server that's being accessed. We also still need to maintain the SSL certificate for
        # hurlstor.soest.hawaii.edu - if it expires, the proxy will fail the SSL handshake.
