import os
from flask import render_template, request, redirect, flash

from application import app
from image_loader import ImageLoader
from annosaurus import *

ANNOSAURUS_URL = os.environ.get('ANNOSAURUS_URL')
ANNOSAURUS_CLIENT_SECRET = os.environ.get('ANNOSAURUS_CLIENT_SECRET')

app.secret_key = 'darc'

# get concept list from vars (for input validation)
with requests.get('http://hurlstor.soest.hawaii.edu:8083/kb/v1/concept') as r:
    vars_concepts = r.json()

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
    rank = None
    phylogeny = None
    for key, val in request.args.items():
        if key != 'rank' and key != 'phylogeny':
            sequences.append(val)
    for sequence_name in sequences:
        if sequence_name not in video_sequences:
            return render_template('404.html', err='dive'), 404
    if 'rank' in request.args.keys():
        rank = request.args.get('rank').lower()
        phylogeny = request.args.get('phylogeny')
    image_loader = ImageLoader(sequences, rank, phylogeny)
    if len(image_loader.distilled_records) < 1:
        return render_template('404.html', err='pics'), 404
    data = {'annotations': image_loader.distilled_records, 'concepts': vars_concepts}
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

    success = annosaurus.update_annotation(
        observation_uuid=request.values.get('observation_uuid'),
        updated_annotation=updated_annotation,
        client_secret=ANNOSAURUS_CLIENT_SECRET
    )
    if success:
        flash('Annotation successfully updated')
    else:
        flash('Failed to update annotation - please try again')

    return redirect(f'dive{request.values.get("params")}')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', err=''), 404
