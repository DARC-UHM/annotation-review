import webbrowser
from threading import Timer

from flask import Flask, render_template, request, redirect, url_for
from jinja2 import Environment, FileSystemLoader
from image_loader import ImageLoader
from annosaurus import *
from env.env import *

# initialize a flask object
app = Flask(__name__)
env = Environment(loader=FileSystemLoader('templates/'))
home = env.get_template('index.html')
images = env.get_template('image_review.html')
err404 = env.get_template('404.html')

# get concept list from vars (for input validation)
with requests.get('http://hurlstor.soest.hawaii.edu:8083/kb/v1/concept') as r:
    vars_concepts = r.json()

# get list of sequences from vars
with requests.get('http://hurlstor.soest.hawaii.edu:8084/vam/v1/videosequences/names') as r:
    video_sequences = r.json()


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.route('/')
def index():
    # return the rendered template
    return render_template(home, sequences=video_sequences)


@app.get('/dive')
def view_images():
    # get images in sequence
    sequences = []
    for key, val in request.args.items():
        sequences.append(val)
    for sequence_name in sequences:
        if sequence_name not in video_sequences:
            return render_template(err404, err='dive'), 404
    image_loader = ImageLoader(sequences)
    if len(image_loader.distilled_records) < 1:
        return render_template(err404, err='pics'), 404
    data = {
        'annotations': image_loader.distilled_records,
        'concepts': vars_concepts,
        'num_records': len(image_loader.distilled_records)
    }
    return render_template(images, data=data)


@app.post('/update_annotation')
def update_annotation():
    annosaurus = Annosaurus(ANNOSAURUS_URL)
    updated_annotation = {
        'concept': request.values.get('editConceptName'),
        'identity-certainty': request.values.get('editIdCert'),
        'identity-reference': request.values.get('editIdRef'),
        'upon': request.values.get('editUpon'),
        'comment': request.values.get('editComments'),
        'guide-photo': request.values.get('editGuidePhoto'),
    }

    annosaurus.update_annotation(
        observation_uuid=request.values.get('observation_uuid'),
        updated_annotation=updated_annotation,
        client_secret=ANNOSAURUS_CLIENT_SECRET
    )

    return redirect(f'dive?sequence={request.values.get("sequenceName")}')


@app.errorhandler(404)
def page_not_found(e):
    return render_template(err404, err=''), 404


def open_browser():
    #webbrowser.open_new('http://127.0.0.1:8000')
    print('\n\033[1;32;48mApplication running. Press CTRL + C to stop.\033[1;37;0m\n')


print('\nLaunching application...')
Timer(1, open_browser).start()

# check to see if this is the main thread of execution
if __name__ == '__main__':
    app.run()
