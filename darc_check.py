import webbrowser
import requests
from flask import Flask, render_template, request, redirect, url_for
from jinja2 import Environment, FileSystemLoader
from image_loader import ImageLoader

# initialize a flask object
app = Flask(__name__)
env = Environment(loader=FileSystemLoader('templates/'))
home = env.get_template('index.html')
images = env.get_template('internal_review.html')

# get concept list from vars (for input validation)
with requests.get('http://hurlstor.soest.hawaii.edu:8083/kb/v1/concept') as r:
    vars_concepts = r.json()


@app.route('/')
def index():
    # return the rendered template
    return render_template(home)


@app.post('/view_images')
def view_images():
    # get images in sequence
    image_loader = ImageLoader([request.values.get('sequenceName')])
    data = {'annotations': image_loader.distilled_records, 'concepts': vars_concepts}
    # return the rendered template
    return render_template(images, data=data)


@app.post('/update_annotation')
def update_annotation():
    image_loader = ImageLoader([request.values.get('sequenceName')])
    
    print(request.values)

    # get updated annotation from request
    # delete old annotation
    # push new annotation

    data = {'annotations': image_loader.distilled_records, 'concepts': vars_concepts, 'messages': 'Annotation updated!'}
    return render_template(images, data=data)


def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000')


# check to see if this is the main thread of execution
if __name__ == '__main__':
    # Timer(1, open_browser).start()
    app.run(debug=True)
