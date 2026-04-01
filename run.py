import os
import webbrowser

from application import create_app
from application.util.constants import TERM_NORMAL, TERM_GREEN

app = create_app()

if __name__ == '__main__':
    print('\nLaunching application...')

    PORT = 8000
    env = os.environ.get('_FLASK_ENV')

    if env in ('development', 'no_server_edits'):
        app.run(debug=True, port=PORT)
    else:
        webbrowser.open_new(f'http://localhost:{PORT}')
        print(f'\n{TERM_GREEN}Application running. Press CTRL + C to stop.{TERM_NORMAL}\n')
        app.run(port=PORT)
