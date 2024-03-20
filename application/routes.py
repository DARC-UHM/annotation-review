import base64
import tator

from io import BytesIO
from flask import render_template, request, redirect, flash, session, Response
from json import JSONDecodeError

from application import app
from application.server.functions import get_association
from application.server.annotation_processor import AnnotationProcessor
from application.server.comment_processor import CommentProcessor
from application.server.tator_qaqc_processor import TatorQaqcProcessor
from application.server.vars_qaqc_processor import VarsQaqcProcessor
from application.server.localization_processor import LocalizationProcessor
from application.server.annosaurus import *

# TODO add location information to localizations once they are updated in Tator
# TODO add method of syncing location data from file
# TODO add bulk editor (lower priority)


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.route('/')
def index():
    unread_comments = 0
    total_comments = 0
    active_reviewers = []
    try:
        # get list of reviewers from external review db
        with requests.get(
                f'{app.config.get("DARC_REVIEW_URL")}/reviewer/all',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
        ) as req:
            session['reviewers'] = req.json()
        # get stats from external review db
        with requests.get(
                f'{app.config.get("DARC_REVIEW_URL")}/stats',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
        ) as r:
            res = r.json()
            unread_comments = res['unread_comments']
            read_comments = res['read_comments']
            total_comments = res['total_comments']
            active_reviewers = res['active_reviewers']
    except (JSONDecodeError, KeyError, requests.exceptions.ConnectionError):
        flash('Unable to connect to external review server', 'danger')
        print('\nERROR: unable to connect to external review server\n')
        session['reviewers'] = []
    try:
        # get list of sequences from vars
        with requests.get(f'{app.config.get("HURLSTOR_URL")}:8084/vam/v1/videosequences/names') as req:
            session['vars_video_sequences'] = req.json()
        # get concept list from vars (for input validation)
        with requests.get(f'{app.config.get("HURLSTOR_URL")}:8083/kb/v1/concept') as req:
            session['vars_concepts'] = req.json()
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to VARS\n')
        flash('Unable to connect to VARS', 'danger')
        session['vars_video_sequences'] = []
        session['vars_concepts'] = []
    return render_template(
        'index.html',
        sequences=session['vars_video_sequences'],
        unread_comment_count=unread_comments,
        read_comment_count=read_comments,
        total_comment_count=total_comments,
        active_reviewers=active_reviewers,
    )


# get token from tator
@app.post('/tator/login')
def tator_login():
    req = requests.post(
            f'{app.config.get("TATOR_URL")}/rest/Token',
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
@app.get('/tator/check-token')
def check_tator_token():
    if 'tator_token' not in session.keys():
        return {}, 400
    try:
        api = tator.get_api(host=app.config.get('TATOR_URL'), token=session['tator_token'])
        print(session['tator_token'])
        return {'username': api.whoami().username}, 200
    except tator.openapi.tator_openapi.exceptions.ApiException:
        return {}, 400


# clears stored tator token
@app.get('/tator/logout')
def tator_logout():
    session.pop('tator_token', None)
    return {}, 200


# get a list of projects associated with user from tator
@app.get('/tator/projects')
def tator_projects():
    try:
        project_list = tator.get_api(
            host=app.config.get('TATOR_URL'),
            token=session['tator_token'],
        ).get_project_list()
        return [{'id': project.id, 'name': project.name} for project in project_list], 200
    except tator.openapi.tator_openapi.exceptions.ApiException:
        return {}, 400


# get a list of sections associated with a project from tator
@app.get('/tator/sections/<project_id>')
def tator_sections(project_id):
    try:
        section_list = tator.get_api(
            host=app.config.get('TATOR_URL'),
            token=session['tator_token'],
        ).get_section_list(project_id)
        return [{'id': section.id, 'name': section.name} for section in section_list], 200
    except tator.openapi.tator_openapi.exceptions.ApiException:
        return {}, 400


# get a list of deployments associated with a project & section from tator
@app.get('/tator/deployments/<project_id>/<section_id>')
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
            media_name = media['name'].split('_')
            # stupid solution until we decide on an actual naming convention
            if len(media_name) == 3:  # format DOEX0087_NIU-dscm-02_c009.mp4
                media_name = media_name[1]
            else:  # format HAW_dscm_01_c010_202304250123Z_0983m.mp4
                media_name = '_'.join(media_name[0:3])
            if media_name not in deployment_list.keys():
                deployment_list[media_name] = [media['id']]
            else:
                deployment_list[media_name].append(media['id'])
        session[f'{project_id}_{section_id}'] = deployment_list
        return sorted(deployment_list.keys()), 200


# view all Tator annotations (localizations) in a specified project & section
@app.get('/tator/image-review/<project_id>/<section_id>')
def tator_image_review(project_id, section_id):
    if 'tator_token' not in session.keys():
        return redirect('/')
    try:
        api = tator.get_api(host=app.config.get('TATOR_URL'), token=session['tator_token'])
        localization_processor = LocalizationProcessor(
            project_id=project_id,
            section_id=section_id,
            api=api,
            deployment_list=request.args.getlist('deployment')
        )
    except tator.openapi.tator_openapi.exceptions.ApiException:
        flash('Please log in to Tator', 'info')
        return redirect('/')
    comments = {}
    deployments = request.args.getlist('deployment')
    # get comments from external review db
    try:
        for deployment in deployments:
            with requests.get(
                f'{app.config.get("DARC_REVIEW_URL")}/comment/sequence/{deployment}',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
            ) as r:
                comments = comments | r.json()  # merge dicts
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to external review server\n')
    data = {
        'annotations': localization_processor.distilled_records,
        'title': localization_processor.section_name,
        'concepts': session['vars_concepts'],
        'reviewers': session['reviewers'],
        'comments': comments,
    }
    return render_template('image-review/image-review.html', data=data)


# view all Tator annotations (localizations) in a specified project & section
@app.get('/tator/qaqc-checklist/<project_id>/<section_id>')
def tator_qaqc_checklist(project_id, section_id):
    if 'tator_token' not in session.keys():
        flash('Please log in to Tator', 'info')
        return redirect('/')
    try:
        api = tator.get_api(host=app.config.get('TATOR_URL'), token=session['tator_token'])
        section_name = api.get_section(id=section_id).name
    except tator.openapi.tator_openapi.exceptions.ApiException:
        flash('Please log in to Tator', 'info')
        return redirect('/')
    media_ids = []
    localizations = []
    individual_count = 0
    for deployment in request.args.getlist('deployment'):
        media_ids += session[f'{project_id}_{section_id}'][deployment]
    # REST is much faster than Python API for large queries
    # adding too many media ids results in a query that is too long, so we have to break it up
    for i in range(0, len(media_ids), 300):
        chunk = media_ids[i:i + 300]
        req = requests.get(
            f'https://cloud.tator.io/rest/Localizations/{project_id}?media_id={",".join(map(str, chunk))}',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Token {session["tator_token"]}',
            })
        localizations += req.json()
    for localization in localizations:
        if localization['type'] == 49:
            individual_count += 1
            if localization['attributes']['Categorical Abundance'] != '--':
                match localization['attributes']['Categorical Abundance']:
                    case '20-49':
                        individual_count += 35
                    case '50-99':
                        individual_count += 75
                    case '100-999':
                        individual_count += 500
                    case '1000+':
                        individual_count += 1000
    data = {
        'title': section_name,
        'localization_count': len(localizations),
        'individual_count': individual_count,
    }
    return render_template('qaqc/tator/qaqc-checklist.html', data=data)


# individual qaqc checks (Tator)
@app.get('/tator/qaqc/<project_id>/<section_id>/<check>')
def tator_qaqc(project_id, section_id, check):
    if 'tator_token' not in session.keys():
        flash('Please log in to Tator', 'info')
        return redirect('/')
    try:
        api = tator.get_api(host=app.config.get('TATOR_URL'), token=session['tator_token'])
    except tator.openapi.tator_openapi.exceptions.ApiException:
        flash('Please log in to Tator', 'info')
        return redirect('/')
    # get comments from external review db
    comments = {}
    try:
        for deployment in request.args.getlist('deployment'):
            with requests.get(
                f'{app.config.get("DARC_REVIEW_URL")}/comment/sequence/{deployment}',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
            ) as r:
                comments = comments | r.json()  # merge dicts
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to external review server\n')
    data = {
        'concepts': session['vars_concepts'],
        'title': check.replace('-', ' ').title(),
        'comments': comments,
        'reviewers': session['reviewers'],
    }
    if check == 'media-attributes':
        # the one case where we don't want to initialize a TatorQaqcProcessor (no need to fetch localizations)
        media_attributes = {}
        for deployment in request.args.getlist('deployment'):
            media_attributes[deployment] = []
            req = requests.get(  # REST API is much faster than Python API for large queries
                f'https://cloud.tator.io/rest/Medias/{project_id}?section={section_id}&attribute_contains=%24name%3A%3A{deployment}',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Token {session["tator_token"]}',
                })
            if req.status_code != 200:
                raise tator.openapi.tator_openapi.exceptions.ApiException
            for media in req.json():
                media_attributes[deployment].append(media)
        data['page_title'] = 'Media attributes'
        data['media_attributes'] = media_attributes
        return render_template('qaqc/tator/qaqc-tables.html', data=data)
    qaqc_annos = TatorQaqcProcessor(
        project_id=project_id,
        section_id=section_id,
        api=api,
        deployment_list=request.args.getlist('deployment'),
    )
    match check:
        case 'names-accepted':
            qaqc_annos.check_names_accepted()
            data['page_title'] = 'Scientific names/tentative IDs not accepted in WoRMS'
        case 'missing-qualifier':
            qaqc_annos.check_missing_qualifier()
            data['page_title'] = 'Records classified higher than species missing qualifier'
        case 'stet-missing-reason':
            qaqc_annos.check_stet_reason()
            data['page_title'] = 'Records with a qualifier of \'stet\' missing \'Reason\''
        case 'attracted-not-attracted':
            attracted_dict = requests.get(f'{app.config.get("DARC_REVIEW_URL")}/attracted').json()
            qaqc_annos.check_attracted_not_attracted(attracted_dict)
            data['page_title'] = 'Attracted/not attracted match expected taxa list (also flags records with taxa that can be either)'
        case 'all-tentative-ids':
            qaqc_annos.get_all_tentative_ids()
            data['page_title'] = 'Records with a tentative ID (also checks phylogeny vs. scientific name)'
        case 'notes-and-remarks':
            qaqc_annos.get_all_notes_and_remarks()
            data['page_title'] = 'Records with notes and/or remarks'
        case 'unique-taxa':
            qaqc_annos.get_unique_taxa()
            data['page_title'] = 'All unique taxa'
            data['unique_taxa'] = qaqc_annos.final_records
            return render_template('qaqc/tator/qaqc-tables.html', data=data)
        case 'summary':
            qaqc_annos.get_summary()
            data['page_title'] = 'Summary'
            data['annotations'] = qaqc_annos.final_records
            return render_template('qaqc/tator/qaqc-tables.html', data=data)
        case _:
            return render_template('not-found.html', err=''), 404
    data['annotations'] = qaqc_annos.final_records
    return render_template('qaqc/tator/qaqc.html', data=data)


# view tator video frame (not cropped)
@app.get('/tator/frame/<media_id>/<frame>')
def tator_frame(media_id, frame):
    if 'tator_token' in session.keys():
        token = session['tator_token']
    else:
        token = request.args.get('token')
    req = requests.get(
        f'{app.config.get("TATOR_URL")}/rest/GetFrame/{media_id}?frames={frame}',
        headers={'Authorization': f'Token {token}'}
    )
    if req.status_code == 200:
        base64_image = base64.b64encode(req.content).decode('utf-8')
        return Response(base64.b64decode(base64_image), content_type='image/png'), 200
    return '', 500


# update tator localization
@app.patch('/tator/localization')
def update_tator_localization():
    localization_id_types = json.loads(request.values.get('localization_id_types'))
    attributes = {
        'Scientific Name': request.values.get('scientific_name'),
        'Qualifier': request.values.get('qualifier'),
        'Reason': request.values.get('reason'),
        'Tentative ID': request.values.get('tentative_id'),
        'IdentificationRemarks': request.values.get('identification_remarks'),
        'Identified By': request.values.get('identified_by'),
        'Notes': request.values.get('notes'),
        'Attracted': request.values.get('attracted'),
    }
    try:
        for localization in localization_id_types:
            this_attributes = attributes.copy()
            if localization['type'] == 49:  # point annotation, add cat abundance
                this_attributes['Categorical Abundance'] = request.values.get('categorical_abundance') if request.values.get('categorical_abundance') else '--'
            api = tator.get_api(host=app.config.get('TATOR_URL'), token=session['tator_token'])
            api.update_localization(
                id=localization['id'],
                localization_update=tator.models.LocalizationUpdate(
                    attributes=this_attributes,
                )
            )
    except tator.openapi.tator_openapi.exceptions.ApiException:
        return {}, 500
    return {}, 200


# view VARS annotations with images in a specified dive (or dives)
@app.get('/vars/image-review')
def view_images():
    comments = {}
    sequences = request.args.getlist('sequence')
    # get comments from external review db
    try:
        for sequence in sequences:
            with requests.get(
                f'{app.config.get("DARC_REVIEW_URL")}/comment/sequence/{sequence}',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
            ) as r:
                comments = comments | r.json()  # merge dicts
            if sequence not in session['vars_video_sequences']:
                return render_template('not-found.html', err='dive'), 404
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to external review server\n')
    # get images in sequence
    image_loader = AnnotationProcessor(sequences)
    if len(image_loader.distilled_records) < 1:
        return render_template('not-found.html', err='pics'), 404
    data = {
        'annotations': image_loader.distilled_records,
        'title': image_loader.vessel_name,
        'concepts': session['vars_concepts'],
        'reviewers': session['reviewers'],
        'comments': comments,
    }
    return render_template('image-review/image-review.html', data=data)


# qaqc checklist page
@app.get('/vars/qaqc-checklist')
def vars_qaqc_checklist():
    sequences = request.args.getlist('sequence')
    annotation_count = 0
    individual_count = 0
    identity_references = set()
    for sequence in sequences:
        with requests.get(f'{app.config.get("HURLSTOR_URL")}:8086/query/dive/{sequence.replace(" ", "%20")}') as r:
            annotation_count += len(r.json()['annotations'])
            for annotation in r.json()['annotations']:
                id_ref = get_association(annotation, 'identity-reference')
                if id_ref:
                    if id_ref['link_value'] in identity_references:
                        continue
                    else:
                        identity_references.add(id_ref['link_value'])
                cat_abundance = get_association(annotation, 'categorical-abundance')
                if cat_abundance:
                    match cat_abundance['link_value']:
                        case '11-20':
                            individual_count += 15
                        case '21-50':
                            individual_count += 35
                        case '51-100':
                            individual_count += 75
                        case '\u003e100':
                            individual_count += 100
                    continue
                pop_quantity = get_association(annotation, 'population-quantity')
                if pop_quantity and pop_quantity['link_value'] != '':
                    individual_count += int(pop_quantity['link_value'])
                    continue
                individual_count += 1
    return render_template('qaqc/vars/qaqc-checklist.html', annotation_count=annotation_count, individual_count=individual_count)


# individual qaqc checks (VARS)
@app.get('/vars/qaqc/<check>')
def vars_qaqc(check):
    sequences = request.args.getlist('sequence')
    qaqc_annos = VarsQaqcProcessor(sequences)
    data = {
        'concepts': session['vars_concepts'],
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
        case 'blank-associations':
            qaqc_annos.find_blank_associations()
            data['page_title'] = 'Records with blank association link values'
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
            return render_template('qaqc/vars/qaqc-unique.html', data=data)
    data['annotations'] = qaqc_annos.final_records
    return render_template('qaqc/vars/qaqc.html', data=data)


@app.get('/vars/qaqc/quick/<check>')
def qaqc_quick(check):
    sequences = request.args.getlist('sequence')
    qaqc_annos = VarsQaqcProcessor(sequences)
    match check:
        case 'missing-ancillary-data':
            records = qaqc_annos.get_num_records_missing_ancillary_data()
            return {'num_records': records}, 200
    return render_template('not-found.html', err=''), 404


# displays all comments in the external review db
@app.get('/external-review')
def get_external_review():
    comments = []
    if 'tator_token' not in session.keys():
        flash('Please log in to Tator', 'info')
        return redirect('/')
    try:
        tator.get_api(host=app.config.get('TATOR_URL'), token=session['tator_token'])
    except tator.openapi.tator_openapi.exceptions.ApiException:
        flash('Please log in to Tator', 'info')
        return redirect('/')
    try:
        # get a list of comments from external review db
        if request.args.get('unread'):
            req = requests.get(
                f'{app.config.get("DARC_REVIEW_URL")}/comment/unread',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
            )
        elif request.args.get('read'):
            req = requests.get(
                f'{app.config.get("DARC_REVIEW_URL")}/comment/read',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
            )
        elif request.args.get('reviewer'):
            req = requests.get(
                f'{app.config.get("DARC_REVIEW_URL")}/comment/reviewer/{request.args.get("reviewer")}',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
            )
        else:
            req = requests.get(
                f'{app.config.get("DARC_REVIEW_URL")}/comment/all',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
            )
        comments = req.json()
        with requests.get(
                f'{app.config.get("DARC_REVIEW_URL")}/stats',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
        ) as r:
            res = r.json()
            unread_comments = res['unread_comments']
            read_comments = res['read_comments']
            total_comments = res['total_comments']
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
        'title': f'External Review {"(" + request.args.get("reviewer") + ")" if request.args.get("reviewer") else ""}',
        'concepts': session['vars_concepts'],
        'reviewers': session['reviewers'],
        'comments': comments,
        'unread_comment_count': unread_comments,
        'read_comment_count': read_comments,
        'total_comment_count': total_comments,
    }
    return render_template('image-review/image-review.html', data=data)


# adds an annotation for review/updates the reviewer for an annotation
@app.post('/external-review')
def add_external_review():
    def add_vars_or_tator_comment(status_code):
        if not request.values.get('scientific_name'):  # VARS annotation, update VARS comment
            annosaurus = Annosaurus(app.config.get('ANNOSAURUS_URL'))
            annosaurus.update_annotation_comment(
                observation_uuid=request.values.get('observation_uuid'),
                reviewers=json.loads(request.values.get('reviewers')),
                client_secret=app.config.get('ANNOSAURUS_CLIENT_SECRET')
            )
        else:  # Tator localization, update Tator notes
            api = tator.get_api(host=app.config.get('TATOR_URL'), token=session['tator_token'])
            current_notes = api.get_localization(id=request.values.get('observation_uuid')).attributes.get('Notes', '').split('|')
            current_notes = [note for note in current_notes if 'send to' not in note.lower()]  # get rid of 'send to expert' notes
            current_notes = [note for note in current_notes if 'added for review' not in note.lower()]  # get rid of old 'added for review' notes
            current_notes = '|'.join(current_notes)
            new_notes = f'{current_notes + "|" if current_notes else ""}Added for review: {", ".join(json.loads(request.values.get("reviewers")))}'
            api.update_localization(
                id=request.values.get('observation_uuid'),
                localization_update=tator.models.LocalizationUpdate(
                    attributes={'Notes': new_notes},
                )
            )
        return {}, status_code
    data = {
        'uuid': request.values.get('observation_uuid'),
        'scientific_name': request.values.get('scientific_name'),
        'all_localizations': request.values.get('all_localizations'),
        'sequence': request.values.get('sequence'),
        'timestamp': request.values.get('timestamp'),
        'image_url': request.values.get('image_url'),
        'reviewers': request.values.get('reviewers'),
        'video_url': request.values.get('video_url'),
        'annotator': request.values.get('annotator'),
        'depth': request.values.get('depth'),
        'lat': request.values.get('lat') ,
        'long': request.values.get('long'),
        'temperature': request.values.get('temperature'),
        'oxygen_ml_l': request.values.get('oxygen_ml_l'),
    }
    image_binary = None
    if request.values.get('scientific_name'):  # tator localization
        # get image so we can post to review server
        req = requests.get(f'{app.config.get("LOCAL_APP_URL")}/{data["image_url"]}?token={session["tator_token"]}')
        if req.status_code == 200:
            image_binary = BytesIO(req.content)
        else:
            return {500: 'Could not get image'}, 500
    with requests.post(
            f'{app.config.get("DARC_REVIEW_URL")}/comment',
            files={'image': (f'{data["uuid"]}.png', image_binary, 'image/png')} if request.values.get('scientific_name') else None,
            headers=app.config.get('DARC_REVIEW_HEADERS'),
            data=data,
    ) as r:
        if r.status_code == 409:  # comment already exists in the db, update record
            req = requests.put(
                f'{app.config.get("DARC_REVIEW_URL")}/comment/reviewers/{data["uuid"]}',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
                data=data,
            )
            if req.status_code == 200:
                return add_vars_or_tator_comment(200)
        elif r.status_code == 201:  # comment added to db, update VARS "comment" field
            return add_vars_or_tator_comment(201)
        return {}, 500


# deletes an item from the external review db
@app.delete('/external-review')
def delete_external_review():
    req = requests.delete(
        f'{app.config.get("DARC_REVIEW_URL")}/comment/{request.values.get("uuid")}',
        headers=app.config.get('DARC_REVIEW_HEADERS'),
    )
    if req.status_code == 200:
        if request.values.get('tator') and request.values.get('tator') == 'true':  # tator localization
            api = tator.get_api(host=app.config.get('TATOR_URL'), token=session['tator_token'])
            current_notes = api.get_localization(id=request.values.get('uuid')).attributes.get('Notes', '').split('|')
            current_notes = [note for note in current_notes if 'send to' not in note.lower()]  # get rid of 'send to expert' notes
            current_notes = [note for note in current_notes if 'added for review' not in note.lower()]  # get rid of old 'added for review' notes
            api.update_localization(
                id=request.values.get('uuid'),
                localization_update=tator.models.LocalizationUpdate(
                    attributes={'Notes': '|'.join(current_notes)},
                )
            )
        else:  # VARS annotation
            annosaurus = Annosaurus(app.config.get('ANNOSAURUS_URL'))
            annosaurus.update_annotation_comment(
                observation_uuid=request.values.get('uuid'),
                reviewers=[],
                client_secret=app.config.get('ANNOSAURUS_CLIENT_SECRET')
            )
        return {}, 200
    return {}, 500


# syncs ctd from vars db with external review db
@app.get('/vars/sync-external-ctd')
def sync_external_ctd():
    updated_ctd = {}
    sequences = {}
    missing_ctd_total = 0
    try:
        req = requests.get(
            f'{app.config.get("DARC_REVIEW_URL")}/comment/all',
            headers=app.config.get('DARC_REVIEW_HEADERS'),
        )
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
        with requests.get(f'{app.config.get("HURLSTOR_URL")}:8086/query/dive/{sequence.replace(" ", "%20")}') as r:
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
    req = requests.put(
        f'{app.config.get("DARC_REVIEW_URL")}/sync-ctd',
        headers=app.config.get('DARC_REVIEW_HEADERS'),
        data=json.dumps(updated_ctd),
    )
    if req.status_code == 200:
        msg = 'CTD synced'
        if missing_ctd_total > 0:
            msg += f' - still missing CTD for {missing_ctd_total} annotation{"s" if missing_ctd_total > 1 else ""}'
        flash(msg, 'success')
    else:
        flash('Unable to sync CTD - please try again', 'danger')
    return redirect('/external-review')


# displays information about all the reviewers in the hurl db
@app.get('/reviewers')
def reviewers():
    return render_template('external-reviewers.html', reviewers=session['reviewers'])


# create or update a reviewer's information
@app.post('/reviewer')
def update_reviewer_info():
    success = False
    name = request.values.get('ogReviewerName') or 'nobody'
    data = {
        'new_name': request.values.get('editReviewerName'),
        'phylum': request.values.get('editPhylum'),
        'focus': request.values.get('editFocus'),
        'organization': request.values.get('editOrganization'),
        'email': request.values.get('editEmail')
    }
    req = requests.patch(
        f'{app.config.get("DARC_REVIEW_URL")}/reviewer/{name}',
        headers=app.config.get('DARC_REVIEW_HEADERS'),
        data=data,
    )
    if req.status_code == 404:
        data['name'] = data['new_name']
        req = requests.post(
            f'{app.config.get("DARC_REVIEW_URL")}/reviewer',
            headers=app.config.get('DARC_REVIEW_HEADERS'),
            data=data,
        )
        if req.status_code == 201:
            success = True
            flash('Successfully added reviewer', 'success')
        else:
            flash('Unable to add reviewer', 'danger')
    elif req.status_code == 200:
        success = True
        flash('Successfully updated reviewer', 'success')
    else:
        flash('Unable to update reviewer', 'danger')
    if success:
        with requests.get(
            f'{app.config.get("DARC_REVIEW_URL")}/reviewer/all',
            headers=app.config.get('DARC_REVIEW_HEADERS'),
        ) as r:
            session['reviewers'] = r.json()
    return redirect('/reviewers')


# delete a reviewer
@app.delete('/reviewer/<name>')
def delete_reviewer(name):
    req = requests.delete(
        f'{app.config.get("DARC_REVIEW_URL")}/reviewer/{name}',
        headers=app.config.get('DARC_REVIEW_HEADERS'),
    )
    if req.status_code == 200:
        flash('Successfully deleted reviewer', 'success')
        with requests.get(
            f'{app.config.get("DARC_REVIEW_URL")}/reviewer/all',
            headers=app.config.get('DARC_REVIEW_HEADERS'),
        ) as req:
            session['reviewers'] = req.json()
    else:
        flash('Error deleting reviewer', 'danger')
    return {}, req.status_code


# updates annotation with new concept name or associations. this is called from the image review page
@app.patch('/vars/annotation')
def update_annotation():
    annosaurus = Annosaurus(app.config.get('ANNOSAURUS_URL'))
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
        client_secret=app.config.get('ANNOSAURUS_CLIENT_SECRET')
    )
    return {}, status


# creates a new association for a VARS annotation
@app.post('/vars/association')
def create_association():
    annosaurus = Annosaurus(app.config.get('ANNOSAURUS_URL'))
    new_association = {
        'link_name': request.values.get('link_name'),
        'link_value': request.values.get('link_value'),
        'to_concept': request.values.get('to_concept'),
    }
    status = annosaurus.create_association(
        observation_uuid=request.values.get('observation_uuid'),
        association=new_association,
        client_secret=app.config.get('ANNOSAURUS_CLIENT_SECRET')
    )
    if status == 200:
        return {}, 201
    return {}, status


# updates a VARS association
@app.patch('/vars/association')
def update_association():
    annosaurus = Annosaurus(app.config.get('ANNOSAURUS_URL'))
    updated_association = {
        'link_name': request.values.get('link_name'),
        'link_value': request.values.get('link_value'),
        'to_concept': request.values.get('to_concept'),
    }
    status = annosaurus.update_association(
        uuid=request.values.get('uuid'),
        association=updated_association,
        client_secret=app.config.get('ANNOSAURUS_CLIENT_SECRET')
    )
    return {}, status


# deletes a VARS association
@app.delete('/vars/association/<uuid>')
def delete_association(uuid):
    annosaurus = Annosaurus(app.config.get('ANNOSAURUS_URL'))
    return {}, annosaurus.delete_association(uuid=uuid, client_secret=app.config.get('ANNOSAURUS_CLIENT_SECRET'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('not-found.html', err=''), 404


@app.get('/video')
def video():
    data = {'link': request.args.get('link'), 'time': request.args.get('time')}
    return render_template('video.html', data=data), 200


def server_error(e):
    error = f'{type(e).__name__}: {e}'
    print('\nApplication error 😔')
    print(error)
    return render_template('error.html', err=error), 500
