import webbrowser
import requests
from threading import Timer
from application import app


def open_browser():
    webbrowser.open_new('http://127.0.0.1:8000')
    print('\n\033[1;32;48mApplication running. Press CTRL + C to stop.\033[1;37;0m\n')


if __name__ == '__main__':
    print('\nLaunching application...')
    Timer(1, open_browser).start()
    app.run()
