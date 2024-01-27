import os
import base64
import tator

from flask import render_template, request, redirect, flash, session, Response
from json import JSONDecodeError
from dotenv import load_dotenv

from application import app
from application.server.image_processor import ImageProcessor
from application.server.comment_processor import CommentProcessor
from application.server.qaqc_processor import QaqcProcessor
from application.server.localization_processor import LocalizationProcessor
from application.server.annosaurus import *

# TODO
#  - VARS: store list of dives in session rather than loading each time
#  - VARS: store VARS concepts in file
#  - VARS/Tator: store concept_phylogeny in file

load_dotenv()

_FLASK_ENV = os.environ.get('_FLASK_ENV')
HURLSTOR_URL = 'http://hurlstor.soest.hawaii.edu'
LOCAL_APP_URL = 'http://127.0.0.1:8000'
TATOR_URL = 'https://cloud.tator.io'

if _FLASK_ENV == 'no_server_edits':
    print('\n\nLOCAL DEVELOPMENT MODE: No server edits\n\n')
    ANNOSAURUS_URL = ''
    ANNOSAURUS_CLIENT_SECRET = ''
    DARC_REVIEW_URL = 'http://127.0.0.1:5000'
else:
    ANNOSAURUS_URL = os.environ.get('ANNOSAURUS_URL')
    ANNOSAURUS_CLIENT_SECRET = os.environ.get('ANNOSAURUS_CLIENT_SECRET')
    DARC_REVIEW_URL = 'https://hurlstor.soest.hawaii.edu:5000'

app.secret_key = os.environ.get('APP_SECRET_KEY')


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.route('/')
def index():
    # get list of sequences from vars
    with requests.get(f'{HURLSTOR_URL}:8084/vam/v1/videosequences/names') as r:
        video_sequences = r.json()
    try:
        with requests.get(f'{DARC_REVIEW_URL}/stats') as r:
            try:
                res = r.json()
                unread_comments = res['unread_comments']
                total_comments = res['total_comments']
                active_reviewers = res['active_reviewers']
            except JSONDecodeError:
                print('Unable to fetch stats from external review server')
                unread_comments = 0
                total_comments = 0
                active_reviewers = []
    except requests.exceptions.ConnectionError:
        unread_comments = 0
        active_reviewers = []
        total_comments = 0
        print('\nERROR: unable to connect to external review server\n')
    return render_template(
        'index.html',
        sequences=video_sequences,
        unread_comment_count=unread_comments,
        total_comment_count=total_comments,
        active_reviewers=active_reviewers
    )


# get token from tator
@app.post('/tator-login')
def tator_login():
    req = requests.post(
            f'{TATOR_URL}/rest/Token',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                'username': request.values.get('username'),
                'password': request.values.get('password'),
                'refresh': True,
            }),
    )
    if req.status_code == 201:
        session['tator_token'] = req.json()['token']
        return {'username': request.values.get('username')}, 200
    return {}, req.status_code


# check if stored tator token is valid
@app.get('/check-tator-token')
def check_tator_token():
    if 'tator_token' not in session.keys():
        return {}, 400
    print(session['tator_token'])  # todo remove
    try:
        api = tator.get_api(host=TATOR_URL, token=session['tator_token'])
        return {'username': api.whoami().username}, 200
    except tator.openapi.tator_openapi.exceptions.ApiException:
        return {}, 400


# clears stored tator token
@app.get('/tator-logout')
def tator_logout():
    session['tator_token'] = None
    return {}, 200


# get a list of projects associated with user from tator
@app.get('/tator-projects')
def tator_projects():
    try:
        project_list = tator.get_api(host=TATOR_URL, token=session['tator_token']).get_project_list()
        return [{'id': project.id, 'name': project.name} for project in project_list], 200
    except tator.openapi.tator_openapi.exceptions.ApiException:
        return {}, 400


# get a list of sections associated with a project from tator
@app.get('/tator-sections/<project_id>')
def tator_sections(project_id):
    try:
        section_list = tator.get_api(host=TATOR_URL, token=session['tator_token']).get_section_list(project_id)
        return [{'id': section.id, 'name': section.name} for section in section_list], 200
    except tator.openapi.tator_openapi.exceptions.ApiException:
        return {}, 400


# get a list of deployments associated with a project & section from tator
@app.get('/tator-deployments/<project_id>/<section_id>')
def load_media(project_id, section_id):
    if f'{project_id}_{section_id}' in session.keys() and request.args.get('refresh') != 'true':
        return sorted(session[f'{project_id}_{section_id}'].keys()), 200
    else:
        deployment_list = {}
        # REST is much faster than Python API for large queries
        req = requests.get(
            f'https://cloud.tator.io/rest/Medias/{project_id}?section={section_id}',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Token {session["tator_token"]}',
            })
        if req.status_code != 200:
            return {}, req.status_code
        for media in req.json():
            if media['name'][:11] not in deployment_list.keys():
                deployment_list[media['name'][:11]] = [media['id']]
            else:
                deployment_list[media['name'][:11]].append(media['id'])
        session[f'{project_id}_{section_id}'] = deployment_list
        return sorted(deployment_list.keys()), 200


# view all Tator annotations (localizations) in a specified project & section
@app.get('/tator-image-review/<project_id>/<section_id>')
def tator_image_review(project_id, section_id):
    if 'tator_token' not in session.keys():
        return redirect('/')
    try:
        api = tator.get_api(host=TATOR_URL, token=session['tator_token'])
        localization_processor = LocalizationProcessor(
            project_id=project_id,
            section_id=section_id,
            api=api,
            deployment_list=request.args.getlist('deployment')
        )
    except tator.openapi.tator_openapi.exceptions.ApiException:
        flash('Please log in to Tator', 'info')
        return redirect('/')
    with requests.get(f'{HURLSTOR_URL}:8083/kb/v1/concept') as r:
        vars_concepts = r.json()
    data = {
        'localizations': localization_processor.distilled_records,
        'section_name': localization_processor.section_name,
        'concepts': vars_concepts,
    }
    return render_template('tator/image-review/image-review.html', data=data)


# view tator localization image, cropped (necessary because images are behind api auth and don't want to expose token)
@app.get('/tator-image/<localization_id>')
def tator_image(localization_id):
    req = requests.get(
        f'{TATOR_URL}/rest/LocalizationGraphic/{localization_id}?use_default_margins=false&margin_x=1000&margin_y=600',
        headers={'Authorization': f'Token {session["tator_token"]}'}
    )
    if req.status_code == 200:
        base64_image = base64.b64encode(req.content).decode('utf-8')
        return Response(base64.b64decode(base64_image), content_type='image/png'), 200
    return '', 500


# view tator video frame (not cropped)
@app.get('/tator-frame/<media_id>/<frame>')
def tator_frame(media_id, frame):
    req = requests.get(
        f'{TATOR_URL}/rest/GetFrame/{media_id}?frames={frame}',
        headers={'Authorization': f'Token {session["tator_token"]}'}
    )
    if req.status_code == 200:
        base64_image = base64.b64encode(req.content).decode('utf-8')
        return Response(base64.b64decode(base64_image), content_type='image/png'), 200
    return '', 500


# view VARS annotations with images in a specified dive (or dives)
@app.get('/vars-image-review')
def view_images():
    comments = {}
    sequences = request.args.getlist('sequence')
    # get list of sequences from vars
    with requests.get(f'{HURLSTOR_URL}:8084/vam/v1/videosequences/names') as r:
        video_sequences = r.json()
    # get concept list from vars (for input validation)
    with requests.get(f'{HURLSTOR_URL}:8083/kb/v1/concept') as r:
        vars_concepts = r.json()
    # get list of reviewers from external review db
    try:
        with requests.get(f'{DARC_REVIEW_URL}/reviewer/all') as r:
            _reviewers = r.json()
        # get comments from the review db
        for sequence in sequences:
            with requests.get(f'{DARC_REVIEW_URL}/comment/sequence/{sequence}') as r:
                comments = comments | r.json()  # merge dicts
            if sequence not in video_sequences:
                return render_template('not-found.html', err='dive'), 404
    except requests.exceptions.ConnectionError:
        _reviewers = []
        print('\nERROR: unable to connect to external review server\n')
    # get images in sequence
    image_loader = ImageProcessor(sequences)
    if len(image_loader.distilled_records) < 1:
        return render_template('not-found.html', err='pics'), 404
    data = {
        'annotations': image_loader.distilled_records,
        'concepts': vars_concepts,
        'reviewers': _reviewers,
        'comments': comments
    }
    return render_template('vars/image-review/image-review.html', data=data)


# qaqc checklist page
@app.get('/vars-qaqc-checklist')
def vars_qaqc_checklist():
    sequences = request.args.getlist('sequence')
    annotation_count = 0
    for sequence in sequences:
        with requests.get(f'{HURLSTOR_URL}:8086/query/dive/{sequence.replace(" ", "%20")}') as r:
            annotation_count += len(r.json()['annotations'])
    return render_template('vars/qaqc/qaqc-checklist.html', annotation_count=annotation_count)


# individual qaqc checks
@app.get('/vars-qaqc/<check>')
def vars_qaqc(check):
    sequences = request.args.getlist('sequence')
    qaqc_annos = QaqcProcessor(sequences)
    # get concept list from vars (for input validation)
    with requests.get(f'{HURLSTOR_URL}:8083/kb/v1/concept') as r:
        vars_concepts = r.json()
    data = {
        'concepts': vars_concepts,
        'title': check.replace('-', ' ').title(),
    }
    match check:
        case 'multiple-associations':
            qaqc_annos.find_duplicate_associations()
            data['page_title'] = 'Records with multiples of the same association other than s2'
        case 'missing-primary-substrate':
            qaqc_annos.find_missing_s1()
            data['page_title'] = 'Records missing primary substrate'
        case 'identical-s1-&-s2':
            qaqc_annos.find_identical_s1_s2()
            data['page_title'] = 'Records with identical primary and secondary substrates'
        case 'duplicate-s2':
            qaqc_annos.find_duplicate_s2()
            data['page_title'] = 'Records with with duplicate secondary substrates'
        case 'missing-upon-substrate':
            qaqc_annos.find_missing_upon_substrate()
            data['page_title'] = 'Records missing a substrate that it is recorded "upon"'
        case 'mismatched-substrates':
            qaqc_annos.find_mismatched_substrates()
            data['page_title'] = 'Records occurring at the same timestamp with mismatched substrates'
        case 'missing-upon':
            qaqc_annos.find_missing_upon()
            data['page_title'] = 'Records other than "none" missing "upon"'
        case 'missing-ancillary-data':
            qaqc_annos.find_missing_ancillary_data()
            data['page_title'] = 'Records missing ancillary data'
        case 'id-ref-concept-name':
            qaqc_annos.find_id_refs_different_concept_name()
            data['page_title'] = 'Records with the same ID reference that have different concept names'
        case 'id-ref-associations':
            qaqc_annos.find_id_refs_conflicting_associations()
            data['page_title'] = 'Records with the same ID reference that have conflicting associations'
        case 'suspicious-hosts':
            qaqc_annos.find_suspicious_hosts()
            data['page_title'] = 'Records with suspicious hosts'
        case 'expected-associations':
            qaqc_annos.find_missing_expected_association()
            data['page_title'] = 'Records expected to be associated with an organism but "upon" is inanimate'
        case 'host-associate-time-diff':
            qaqc_annos.find_long_host_associate_time_diff()
            data['page_title'] = 'Records where "upon" occurred more than one minute ago or cannot be found'
        case 'unique-fields':
            qaqc_annos.find_unique_fields()
            data['unique_list'] = qaqc_annos.final_records
            return render_template('vars/qaqc/qaqc-unique.html', data=data)
    data['annotations'] = qaqc_annos.final_records
    return render_template('vars/qaqc/qaqc.html', data=data)


@app.get('/vars-qaqc/quick/<check>')
def qaqc_quick(check):
    sequences = request.args.getlist('sequence')
    qaqc_annos = QaqcProcessor(sequences)
    match check:
        case 'missing-ancillary-data':
            records = qaqc_annos.get_num_records_missing_ancillary_data()
            return {'num_records': records}, 200
    return render_template('not-found.html', err=''), 404


# displays all comments in the external review db
@app.get('/external-review')
def external_review():
    comments = []
    # get concept list from vars (for input validation)
    with requests.get(f'{HURLSTOR_URL}:8083/kb/v1/concept') as r:
        vars_concepts = r.json()
    # get list of reviewers from external review db
    try:
        with requests.get(f'{DARC_REVIEW_URL}/reviewer/all') as r:
            _reviewers = r.json()
        # get a list of comments from external review db
        if request.args.get('unread'):
            req = requests.get(f'{DARC_REVIEW_URL}/comment/unread')
        elif request.args.get('reviewer'):
            req = requests.get(f'{DARC_REVIEW_URL}/comment/reviewer/{request.args.get("reviewer")}')
        else:
            req = requests.get(f'{DARC_REVIEW_URL}/comment/all')
        comments = req.json()
    except requests.exceptions.ConnectionError:
        _reviewers = []
        print('\nERROR: unable to connect to external review server\n')
    comment_loader = CommentProcessor(comments)
    if len(comment_loader.distilled_records) < 1:
        if request.args.get('unread'):
            return render_template('not-found.html', err='unread'), 404
        return render_template('not-found.html', err='comments'), 404
    data = {
        'annotations': comment_loader.distilled_records,
        'concepts': vars_concepts,
        'reviewers': _reviewers,
        'comments': comments
    }
    return render_template('vars/image-review/image-review.html', data=data)


# syncs ctd from vars db with external review db
@app.get('/sync-external-ctd')
def sync_external_ctd():
    updated_ctd = {}
    sequences = {}
    missing_ctd_total = 0
    try:
        req = requests.get(f'{DARC_REVIEW_URL}/comment/all')
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to external review server\n')
        flash('Unable to connect to external review server', 'danger')
        return redirect('/')
    comments = req.json()
    for key, val in comments.items():
        if val['sequence'] not in sequences.keys():
            sequences[val['sequence']] = [key]
        else:
            sequences[val['sequence']].append(key)
    for sequence in sequences.keys():
        with requests.get(f'{HURLSTOR_URL}:8086/query/dive/{sequence.replace(" ", "%20")}') as r:
            response = r.json()
            for annotation in response['annotations']:
                if annotation['observation_uuid'] in sequences[sequence]:
                    if 'ancillary_data' in annotation.keys():
                        updated_ctd[annotation['observation_uuid']] = {
                            'depth': round(annotation['ancillary_data']['depth_meters']) if 'depth_meters' in annotation['ancillary_data'].keys() else None,
                            'lat': round(annotation['ancillary_data']['latitude'], 3) if 'latitude' in annotation['ancillary_data'].keys() else None,
                            'long': round(annotation['ancillary_data']['longitude'], 3) if 'longitude' in annotation['ancillary_data'].keys() else None,
                            'temperature': round(annotation['ancillary_data']['temperature_celsius'], 2) if 'temperature_celsius' in annotation['ancillary_data'].keys() else None,
                            'oxygen_ml_l': round(annotation['ancillary_data']['oxygen_ml_l'], 3) if 'oxygen_ml_l' in annotation['ancillary_data'].keys() else None,
                        }
                    else:
                        missing_ctd_total += 1
    req = requests.put(f'{DARC_REVIEW_URL}/sync-ctd', data=json.dumps(updated_ctd))
    if req.status_code == 200:
        msg = 'CTD synced'
        if missing_ctd_total > 0:
            msg += f' - still missing CTD for {missing_ctd_total} annotation{"s" if missing_ctd_total > 1 else ""}'
        flash(msg, 'success')
    else:
        flash('Unable to sync CTD - please try again', 'danger')
    return redirect('/external-review')


# deletes an item from the external review db
@app.post('/delete-external-comment')
def delete_external_comment():
    req = requests.delete(f'{DARC_REVIEW_URL}/comment/delete/{request.values.get("uuid")}')
    if req.status_code == 200:
        new_comment = {
            'observation_uuid': request.values.get('uuid'),
            'reviewer': '[]',
            'action': 'DELETE'
        }
        requests.post(f'{LOCAL_APP_URL}/update-annotation-comment', new_comment)
        return {}, 200
    return {}, 500


# displays information about all the reviewers in the hurl db
@app.get('/reviewers')
def reviewers():
    try:
        with requests.get(f'{DARC_REVIEW_URL}/reviewer/all') as r:
            reviewer_list = r.json()
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to external review server\n')
        flash('Unable to connect to external review server', 'danger')
    return render_template('external-reviewers.html', reviewers=reviewer_list)


# update a reviewer's information
@app.post('/update-reviewer-info')
def update_reviewer_info():
    name = request.values.get('ogReviewerName') or 'nobody'
    data = {
        'new_name': request.values.get('editReviewerName'),
        'phylum': request.values.get('editPhylum'),
        'focus': request.values.get('editFocus'),
        'organization': request.values.get('editOrganization'),
        'email': request.values.get('editEmail')
    }
    req = requests.put(f'{DARC_REVIEW_URL}/reviewer/update/{name}', data=data)
    if req.status_code == 404:
        data['name'] = data['new_name']
        req = requests.post(f'{DARC_REVIEW_URL}/reviewer/add', data=data)
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
    req = requests.delete(f'{DARC_REVIEW_URL}/reviewer/delete/{name}')
    if req.status_code == 200:
        flash('Reviewer successfully deleted', 'success')
    else:
        flash('Error deleting reviewer', 'danger')
    return redirect('/reviewers')


# adds an annotation for review/updates the reviewer for an annotation
@app.post('/update-annotation-reviewer')
def update_annotation_reviewer():
    data = {
        'uuid': request.values.get('observation_uuid'),
        'sequence': request.values.get('sequence'),
        'timestamp': request.values.get('timestamp'),
        'image_url': request.values.get('image_url'),
        'reviewers': request.values.get('reviewers'),
        'video_url': request.values.get('video_url'),
        'annotator': request.values.get('annotator'),
        'depth': request.values.get('depth'),
        'lat': request.values.get('lat'),
        'long': request.values.get('long'),
        'temperature': request.values.get('temperature'),
        'oxygen_ml_l': request.values.get('oxygen_ml_l'),
    }
    with requests.post(f'{DARC_REVIEW_URL}/comment/add', data=data) as r:
        if r.status_code == 409:  # comment already exists in the db, update record
            req = requests.put(f'{DARC_REVIEW_URL}/comment/update-reviewers/{data["uuid"]}', data=data)
            if req.status_code == 200:
                new_comment = {
                    'observation_uuid': request.values.get('observation_uuid'),
                    'reviewers': request.values.get("reviewers"),
                    'action': 'ADD'
                }
                requests.post(f'{LOCAL_APP_URL}/update-annotation-comment', new_comment)
                return {}, 200
        elif r.status_code == 201:  # comment added to db, update VARS "comment" field
            new_comment = {
                'observation_uuid': request.values.get('observation_uuid'),
                'reviewers': request.values.get('reviewers'),
                'action': 'ADD'
            }
            requests.post(f'{LOCAL_APP_URL}/update-annotation-comment', new_comment)
            return {}, 201
        return {}, 500


# updates the comment in the vars db to reflect that the record has been added to the comment db
@app.post('/update-annotation-comment')
def update_annotation_comment():
    annosaurus = Annosaurus(ANNOSAURUS_URL)
    annosaurus.update_annotation_comment(
        observation_uuid=request.values.get('observation_uuid'),
        reviewers=request.values.get('reviewers'),
        action=request.values.get('action'),
        client_secret=ANNOSAURUS_CLIENT_SECRET
    )
    return ''


# updates annotation with new concept name or associations. this is called from the image review page
@app.post('/update-annotation')
def update_annotation():
    annosaurus = Annosaurus(ANNOSAURUS_URL)
    updated_annotation = {
        'concept': request.values.get('concept'),
        'identity-certainty': request.values.get('identity-certainty').replace('\'', ''),
        'identity-reference': request.values.get('identity-reference'),
        'upon': request.values.get('upon').replace('\'', ''),
        'comment': request.values.get('comment').replace('\'', ''),
        'guide-photo': request.values.get('guide-photo'),
    }
    status = annosaurus.update_annotation(
        observation_uuid=request.values.get('observation_uuid'),
        updated_annotation=updated_annotation,
        client_secret=ANNOSAURUS_CLIENT_SECRET
    )
    if status == 1:
        return {}, 204
    elif status == 0:
        return {}, 304
    else:
        return {}, 500


# creates a new association for an annotation
@app.post('/create-association')
def create_association():
    annosaurus = Annosaurus(ANNOSAURUS_URL)
    new_association = {
        'link_name': request.values.get('link_name'),
        'link_value': request.values.get('link_value'),
        'to_concept': request.values.get('to_concept'),
    }
    status = annosaurus.create_association(
        observation_uuid=request.values.get('observation_uuid'),
        association=new_association,
        client_secret=ANNOSAURUS_CLIENT_SECRET
    )
    if status == 200:
        return {}, 201
    return {}, status


# updates an association
@app.post('/update-association')
def update_association():
    annosaurus = Annosaurus(ANNOSAURUS_URL)
    updated_association = {
        'link_name': request.values.get('link_name'),
        'link_value': request.values.get('link_value'),
        'to_concept': request.values.get('to_concept'),
    }
    status = annosaurus.update_association(
        uuid=request.values.get('uuid'),
        association=updated_association,
        client_secret=ANNOSAURUS_CLIENT_SECRET
    )
    return {}, status


@app.get('/delete-association/<uuid>')
def delete_association(uuid):
    annosaurus = Annosaurus(ANNOSAURUS_URL)
    return {}, annosaurus.delete_association(uuid=uuid, client_secret=ANNOSAURUS_CLIENT_SECRET)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('not-found.html', err=''), 404


@app.get('/video')
def video():
    data = {'link': request.args.get('link'), 'time': request.args.get('time')}
    return render_template('video.html', data=data), 200


# @app.errorhandler(Exception)
# def server_error(e):
#     error = f'{type(e).__name__}: {e}'
#     print('\nApplication error 😔')
#     print(error)
#     return render_template('error.html', err=error), 500
