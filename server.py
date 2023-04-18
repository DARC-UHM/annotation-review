import webbrowser
from flask import Flask, render_template, request
from jinja2 import Environment, FileSystemLoader

# initialize a flask object
app = Flask(__name__)
env = Environment(loader=FileSystemLoader("templates/"))
home = env.get_template('index.html')
images = env.get_template('photo_review.html')


@app.route("/")
def index():
    # return the rendered template
    return render_template(home)


@app.post("/view_images")
def view_images():
    print(request.values.get('sequenceName'))
    # return the rendered template
    return render_template(images)


def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000')


# check to see if this is the main thread of execution
if __name__ == '__main__':
    # Timer(1, open_browser).start()
    app.run(debug=True)
