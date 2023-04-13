import webbrowser
from threading import Timer
from flask import Flask
from flask import render_template

# initialize a flask object
app = Flask(__name__)


@app.route("/")
def index():
    # return the rendered template
    return render_template("index.html")


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")


# check to see if this is the main thread of execution
if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run()
