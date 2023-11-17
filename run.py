import os

from application import app
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()
    if os.environ.get('_FLASK_ENV') == 'development' or os.environ.get('_FLASK_ENV') == 'no_server_edits':
        app.run(debug=True, port=8000)
    else:
        app.run()
