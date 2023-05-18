import os
from flask import render_template, request, redirect, flash
from dotenv import load_dotenv

from application import app
from image_loader import ImageLoader
from annosaurus import *

load_dotenv()

ANNOSAURUS_URL = os.environ.get('ANNOSAURUS_URL')
ANNOSAURUS_CLIENT_SECRET = os.environ.get('ANNOSAURUS_CLIENT_SECRET')

app.secret_key = 'darc'

# get concept list from vars (for input validation)
with requests.get('http://hurlstor.soest.hawaii.edu:8083/kb/v1/concept') as r:
    vars_concepts = r.json()

# get list of reviewers from external review db
with requests.get('http://localhost:8000/reviewer/all') as r:
    reviewers = r.json()

# get list of sequences from vars
with requests.get('http://hurlstor.soest.hawaii.edu:8084/vam/v1/videosequences/names') as r:
    sequences = r.json()

video_sequences = []
for video in sequences:
    video_sequences.append(video)


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.route('/')
def index():
    # return the rendered template
    return render_template('index.html', sequences=video_sequences)


@app.get('/dive')
def view_images():
    # get images in sequence
    sequences = []
    filter_type = None
    filter_ = None
    for key, val in request.args.items():
        if 'sequence' in key:
            sequences.append(val)
        else:
            filter_type = key
            filter_ = val
    for sequence_name in sequences:
        if sequence_name not in video_sequences:
            return render_template('404.html', err='dive'), 404
    image_loader = ImageLoader(sequences, filter_type, filter_)
    if len(image_loader.distilled_records) < 1:
        return render_template('404.html', err='pics'), 404
    data = {'annotations': image_loader.distilled_records, 'concepts': vars_concepts, 'reviewers': reviewers}
    return render_template('image_review.html', data=data)


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

    status = annosaurus.update_annotation(
        observation_uuid=request.values.get('observation_uuid'),
        updated_annotation=updated_annotation,
        client_secret=ANNOSAURUS_CLIENT_SECRET
    )
    if status == 1:
        flash('Annotation successfully updated', 'success')
    elif status == 0:
        flash('No changes made', 'secondary')
    else:
        flash('Failed to update annotation - please try again', 'danger')

    return redirect(f'dive{request.values.get("params")}')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', err=''), 404
