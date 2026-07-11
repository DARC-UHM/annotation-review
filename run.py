import datetime
import subprocess
import webbrowser

from application import create_app
from application.util.constants import TERM_NORMAL, TERM_GREEN

app = create_app()

if __name__ == '__main__':
    print('\nLaunching application...')

    PORT = 8000

    try:
        app.config['LOCAL_COMMIT_HASH'] = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
        app.config['LAST_CHECKED_ORIGIN_AT'] = datetime.datetime.now().isoformat()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print('Warning: Unable to retrieve local commit hash.')
        pass

    if app.config.get('ENV') in ('development', 'no_server_edits'):
        app.run(debug=True, port=PORT)
    else:
        webbrowser.open_new(f'http://localhost:{PORT}')
        print(f'\n{TERM_GREEN}Application running. Press CTRL + C to stop.{TERM_NORMAL}\n')
        app.run(port=PORT)
