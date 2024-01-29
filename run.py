import os

from application import app

if __name__ == '__main__':
    if os.environ.get('_FLASK_ENV') == 'development' or os.environ.get('_FLASK_ENV') == 'no_server_edits':
        app.run(debug=True, port=8000)
    else:
        app.run()
