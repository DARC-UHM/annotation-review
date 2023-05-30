import os

from flask import render_template, request, redirect, flash
from dotenv import load_dotenv

from application import app
from application.server.comment_loader import CommentLoader
from application.server.image_loader import ImageLoader, parse_datetime
from application.server.annosaurus import *

load_dotenv()

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


# view the annotations with images in a specified dive (or dives) with optional filters
@app.get('/dive')
def view_images():
    # get list of reviewers from external review db
    with requests.get('http://hurlstor.soest.hawaii.edu:5000/reviewer/all') as r:
        reviewers = r.json()
    # get images in sequence
    sequences = []
    comments = {}
    filter_type = None
    filter_ = None
    for key, val in request.args.items():
        if 'sequence' in key:
            sequences.append(val)
            with requests.get(f'http://hurlstor.soest.hawaii.edu:5000/comment/sequence/{val}') as r:
                comments = comments | r.json()  # merge dicts
        else:
            filter_type = key
            filter_ = val
    for sequence_name in sequences:
        if sequence_name not in video_sequences:
            return render_template('404.html', err='dive'), 404
    image_loader = ImageLoader(sequences, filter_type, filter_)
    if len(image_loader.distilled_records) < 1:
        return render_template('404.html', err='pics'), 404
    data = {
        'annotations': image_loader.distilled_records,
        'concepts': vars_concepts,
        'reviewers': reviewers,
        'comments': comments
    }
    return render_template('image_review.html', data=data)


# displays all comments in the external review db
@app.get('/external_review')
def external_review():
    # get list of reviewers from external review db
    with requests.get('http://hurlstor.soest.hawaii.edu:5000/reviewer/all') as r:
        reviewers = r.json()
    # get a list of comments from external review db
    with requests.get('http://hurlstor.soest.hawaii.edu:5000/comment/all') as r:
        comments = r.json()
    comment_loader = CommentLoader(comments)
    if len(comment_loader.annotations) < 1:
        return render_template('404.html', err='pics'), 404
    data = {
        'annotations': comment_loader.annotations,
        'concepts': vars_concepts,
        'reviewers': reviewers,
        'comments': comments
    }
    return render_template('image_review.html', data=data)


# deletes an item from the external review db
@app.post('/delete_external_comment')
def delete_external_comment():
    req = requests.delete(f'http://hurlstor.soest.hawaii.edu:5000/comment/delete/{request.values.get("uuid")}')
    if req.status_code == 200:
        flash('Comment successfully deleted', 'success')
    else:
        flash('Error deleting comment', 'danger')
    if 'sequence' in request.values.get("params"):
        return redirect(f'dive{request.values.get("params")}')
    return redirect(f'/external_review')


# displays information about all the reviewers in the hurl db
@app.get('/reviewers')
def reviewers():
    with requests.get('http://hurlstor.soest.hawaii.edu:5000/reviewer/all') as r:
        reviewer_list = r.json()
    return render_template('reviewers.html', reviewers=reviewer_list)


# update a reviewer's information
@app.post('/update_reviewer_info')
def update_reviewer_info():
    name = request.values.get('ogReviewerName') or 'nobody'
    data = {
        'new_name': request.values.get('editReviewerName'),
        'phylum': request.values.get('editPhylum'),
        'focus': request.values.get('editFocus'),
        'organization': request.values.get('editOrganization'),
        'email': request.values.get('editEmail')
    }
    req = requests.put(f'http://hurlstor.soest.hawaii.edu:5000/reviewer/update/{name}', data=data)
    if req.status_code == 404:
        data['name'] = data['new_name']
        req = requests.post('http://hurlstor.soest.hawaii.edu:5000/reviewer/add', data=data)
        if req.status_code == 201:
            flash('Successfully added reviewer', 'success')
        else:
            flash('Unable to add reviewer', 'danger')
    elif req.status_code == 200:
        flash('Successfully updated reviewer', 'success')
    else:
        flash('Unable to update reviewer', 'danger')
    return redirect('/reviewers')


# delete a reviewer
@app.get('/delete_reviewer/<name>')
def delete_reviewer(name):
    req = requests.delete(f'http://hurlstor.soest.hawaii.edu:5000/reviewer/delete/{name}')
    if req.status_code == 200:
        flash('Reviewer successfully deleted', 'success')
    else:
        flash('Error deleting reviewer', 'danger')
    return redirect('/reviewers')


# updates the reviewer for an annotation in the hurl db
@app.post('/update_annotation_reviewer')
def update_annotation_reviewer():
    data = {
        'uuid': request.values.get('observation_uuid'),
        'sequence': request.values.get('sequence'),
        'timestamp': parse_datetime(request.values.get('timestamp')).strftime('%d %b %y %H:%M:%S UTC'),
        'image_url': request.values.get('image_url'),
        'concept': request.values.get('concept'),
        'reviewer': request.values.get('reviewer'),
        'video_url': request.values.get('video_url'),
        'id_certainty': request.values.get('id_certainty'),
        'id_reference': request.values.get('id_reference'),
        'upon': request.values.get('upon'),
    }
    with requests.post('http://hurlstor.soest.hawaii.edu:5000/comment/add', data=data) as r:
        if r.status_code == 409:
            req = requests.put(f'http://hurlstor.soest.hawaii.edu:5000/comment/update_reviewer/{data["uuid"]}', data=data)
            if req.status_code == 200:
                new_comment = {
                    'observation_uuid': request.values.get('observation_uuid'),
                    'reviewer': request.values.get("reviewer")
                }
                requests.post('http://127.0.0.1:5000/update_annotation_comment', new_comment)
                flash('Reviewer successfully updated', 'success')
            else:
                flash('Failed to update reviewer - please try again', 'danger')
        elif r.status_code == 201:
            new_comment = {
                'observation_uuid': request.values.get('observation_uuid'),
                'reviewer': request.values.get("reviewer")
            }
            requests.post('http://127.0.0.1:5000/update_annotation_comment', new_comment)
            flash('Successfully added for review', 'success')
        else:
            flash('Failed to add for review - please try again', 'danger')

    if 'sequence' in request.values.get("params"):
        return redirect(f'dive{request.values.get("params")}')
    return redirect(f'/external_review')


# updates the comment in the vars db to reflect that the record has been added to the comment db
@app.post('/update_annotation_comment')
def update_annotation_comment():
    annosaurus = Annosaurus(ANNOSAURUS_URL)
    annosaurus.update_annotation_comment(
        observation_uuid=request.values.get('observation_uuid'),
        reviewer=request.values.get('reviewer'),
        client_secret=ANNOSAURUS_CLIENT_SECRET
    )
    return ''


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

    if 'sequence' in request.values.get("params"):
        return redirect(f'dive{request.values.get("params")}')
    return redirect(f'/external_review')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', err=''), 404
