import base64
import tator
import sys
import traceback

from io import BytesIO
from flask import render_template, request, redirect, flash, session, Response, send_file
from json import JSONDecodeError

from application import app
from application.server.vars_annotation_processor import VarsAnnotationProcessor
from application.server.comment_processor import CommentProcessor
from application.server.tator_qaqc_processor import TatorQaqcProcessor
from application.server.vars_qaqc_processor import VarsQaqcProcessor
from application.server.tator_localization_processor import TatorLocalizationProcessor
from application.server.annosaurus import *


@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')


@app.route('/')
def index():
    unread_comments = 0
    read_comments = 0
    total_comments = 0
    active_reviewers = []
    try:
        # get list of reviewers from external review db
        with requests.get(
            url=f'{app.config.get("DARC_REVIEW_URL")}/reviewer/all',
            headers=app.config.get('DARC_REVIEW_HEADERS'),
        ) as reviewers_res:
            session['reviewers'] = reviewers_res.json()
        # get stats from external review db
        with requests.get(
            url=f'{app.config.get("DARC_REVIEW_URL")}/stats',
            headers=app.config.get('DARC_REVIEW_HEADERS'),
        ) as stats_res:
            stats_json = stats_res.json()
            unread_comments = stats_json['unread_comments']
            read_comments = stats_json['read_comments']
            total_comments = stats_json['total_comments']
            active_reviewers = stats_json['active_reviewers']
    except (JSONDecodeError, KeyError, requests.exceptions.ConnectionError):
        flash('Unable to connect to external review server', 'danger')
        print('\nERROR: unable to connect to external review server\n')
        session['reviewers'] = []
    try:
        # get list of sequences from vars
        with requests.get(url=f'{app.config.get("HURLSTOR_URL")}:8084/v1/videosequences/names') as sequences_res:
            session['vars_video_sequences'] = sequences_res.json()
        # get concept list from vars (for input validation)
        with requests.get(url=f'{app.config.get("HURLSTOR_URL")}:8083/v1/concept') as concept_res:
            session['vars_concepts'] = concept_res.json()
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
    res = requests.post(
        url=f'{app.config.get("TATOR_URL")}/rest/Token',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({
            'username': request.values.get('username'),
            'password': request.values.get('password'),
            'refresh': True,
        }),
    )
    if res.status_code == 201:
        session['tator_token'] = res.json()['token']
        return {'username': request.values.get('username')}, 200
    return {}, res.status_code


# check if stored tator token is valid
@app.get('/tator/check-token')
def check_tator_token():
    if 'tator_token' not in session.keys():
        return {}, 400
    try:
        api = tator.get_api(
            host=app.config.get('TATOR_URL'),
            token=session['tator_token'],
        )
        print(f'Your Tator token: {session["tator_token"]}')
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
            token=session.get('tator_token'),
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
            token=session.get('tator_token'),
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
        res = requests.get(
            url=f'https://cloud.tator.io/rest/Medias/{project_id}?section={section_id}',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Token {session.get("tator_token")}',
            })
        if res.status_code != 200:
            return {}, res.status_code
        for media in res.json():
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


# deletes stored tator sections
@app.get('/tator/refresh-sections')
def refresh_tator_sections():
    for key in list(session.keys()):
        if key.split('_')[0] == '26':  # id for NGS-ExTech Project
            session.pop(key)
    return {}, 200


# view all Tator annotations (localizations) in a specified project & section
@app.get('/tator/image-review/<project_id>/<section_id>')
def tator_image_review(project_id, section_id):
    if 'tator_token' not in session.keys():
        return redirect('/')
    try:
        api = tator.get_api(
            host=app.config.get('TATOR_URL'),
            token=session['tator_token'],
        )
        localization_processor = TatorLocalizationProcessor(
            project_id=project_id,
            section_id=section_id,
            api=api,
            deployment_list=request.args.getlist('deployment')
        )
        localization_processor.fetch_localizations()
        localization_processor.load_phylogeny()
        localization_processor.process_records()
    except tator.openapi.tator_openapi.exceptions.ApiException:
        flash('Please log in to Tator', 'info')
        return redirect('/')
    comments = {}
    deployments = request.args.getlist('deployment')
    # get comments from external review db
    try:
        for deployment in deployments:
            with requests.get(
                url=f'{app.config.get("DARC_REVIEW_URL")}/comment/sequence/{deployment.replace("-", "_")}',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
            ) as res:
                comments = comments | res.json()  # merge dicts
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to external review server\n')
    data = {
        'annotations': localization_processor.final_records,
        'title': localization_processor.section_name,
        'concepts': session.get('vars_concepts', []),
        'reviewers': session.get('reviewers', []),
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
        api = tator.get_api(
            host=app.config.get('TATOR_URL'),
            token=session['tator_token'],
        )
        section_name = api.get_section(id=section_id).name
    except tator.openapi.tator_openapi.exceptions.ApiException:
        flash('Please log in to Tator', 'info')
        return redirect('/')
    media_ids = []
    localizations = []
    individual_count = 0
    for deployment in request.args.getlist('deployment'):
        media_ids += session[f'{project_id}_{section_id}'][deployment]
    with requests.get(
        url=f'{app.config.get("DARC_REVIEW_URL")}/tator-qaqc-checklist/{"&".join(request.args.getlist("deployment"))}',
        headers=app.config.get('DARC_REVIEW_HEADERS'),
    ) as checklist_res:
        if checklist_res.status_code == 200:
            checklist = checklist_res.json()
        else:
            print('ERROR: Unable to get QAQC checklist from external review server')
            checklist = {}
    # REST is much faster than Python API for large queries
    # adding too many media ids results in a query that is too long, so we have to break it up
    for i in range(0, len(media_ids), 300):
        chunk = media_ids[i:i + 300]
        res = requests.get(
            url=f'https://cloud.tator.io/rest/Localizations/{project_id}?media_id={",".join(map(str, chunk))}',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Token {session["tator_token"]}',
            })
        localizations += res.json()
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
        'checklist': checklist,
    }
    return render_template('qaqc/tator/qaqc-checklist.html', data=data)


# update tator qaqc checklist
@app.patch('/tator/qaqc-checklist')
def patch_tator_qaqc_checklist():
    req_json = request.json
    deployments = req_json.get('deployments')
    if not deployments:
        return {}, 400
    req_json.pop('deployments')
    res = requests.patch(
        url=f'{app.config.get("DARC_REVIEW_URL")}/tator-qaqc-checklist/{deployments}',
        headers=app.config.get('DARC_REVIEW_HEADERS'),
        json=req_json,
    )
    return res.json(), res.status_code


# individual qaqc checks (Tator)
@app.get('/tator/qaqc/<project_id>/<section_id>/<check>')
def tator_qaqc(project_id, section_id, check):
    if 'tator_token' not in session.keys():
        flash('Please log in to Tator', 'info')
        return redirect('/')
    try:
        api = tator.get_api(
            host=app.config.get('TATOR_URL'),
            token=session['tator_token'],
        )
    except tator.openapi.tator_openapi.exceptions.ApiException:
        flash('Please log in to Tator', 'info')
        return redirect('/')
    # get comments from external review db
    comments = {}
    try:
        for deployment in request.args.getlist('deployment'):
            with requests.get(
                url=f'{app.config.get("DARC_REVIEW_URL")}/comment/sequence/{deployment}',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
            ) as res:
                comments = comments | res.json()  # merge dicts
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to external review server\n')
    data = {
        'concepts': session.get('vars_concepts', []),
        'title': check.replace('-', ' ').title(),
        'comments': comments,
        'reviewers': session.get('reviewers', []),
    }
    if check == 'media-attributes':
        # the one case where we don't want to initialize a TatorQaqcProcessor (no need to fetch localizations)
        media_attributes = {}
        for deployment in request.args.getlist('deployment'):
            media_attributes[deployment] = []
            res = requests.get(  # REST API is much faster than Python API for large queries
                url=f'https://cloud.tator.io/rest/Medias/{project_id}?section={section_id}&attribute_contains=%24name%3A%3A{deployment}',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Token {session["tator_token"]}',
                })
            if res.status_code != 200:
                raise tator.openapi.tator_openapi.exceptions.ApiException
            for media in res.json():
                media_attributes[deployment].append(media)
        data['page_title'] = 'Media attributes'
        data['media_attributes'] = media_attributes
        return render_template('qaqc/tator/qaqc-tables.html', data=data)
    qaqc_annos = TatorQaqcProcessor(
        project_id=project_id,
        section_id=section_id,
        api=api,
        deployment_list=request.args.getlist('deployment'),
        darc_review_url=app.config.get('DARC_REVIEW_URL'),
    )
    qaqc_annos.fetch_localizations()
    qaqc_annos.load_phylogeny()
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
            attracted_concepts = requests.get(url=f'{app.config.get("DARC_REVIEW_URL")}/attracted').json()
            qaqc_annos.check_attracted_not_attracted(attracted_concepts)
            data['page_title'] = 'Attracted/not attracted match expected taxa list'
            data['attracted_concepts'] = attracted_concepts
        case 'same-name-qualifier':
            qaqc_annos.check_same_name_qualifier()
            data['page_title'] = 'Records with the same scientific name/tentative ID but different qualifiers'
        case 'non-target-not-attracted':
            qaqc_annos.check_non_target_not_attracted()
            data['page_title'] = '"Non-target" records marked as "attracted"'
        case 'all-tentative-ids':
            qaqc_annos.get_all_tentative_ids()
            data['page_title'] = 'Records with a tentative ID (also checks phylogeny vs. scientific name)'
        case 'notes-and-remarks':
            qaqc_annos.get_all_notes_and_remarks()
            data['page_title'] = 'Records with notes and/or remarks'
        case 're-examined':
            qaqc_annos.get_re_examined()
            data['page_title'] = 'Records marked "to be re-examined"'
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
        case 'max-n':
            qaqc_annos.get_max_n()
            data['page_title'] = 'Max N'
            data['max_n'] = qaqc_annos.final_records
            return render_template('qaqc/tator/qaqc-tables.html', data=data)
        case 'tofa':
            qaqc_annos.get_tofa()
            data['page_title'] = 'Time of First Arrival'
            data['tofa'] = qaqc_annos.final_records
            return render_template('qaqc/tator/qaqc-tables.html', data=data)
        case 'image-guide':
            presentation_data = BytesIO()
            qaqc_annos.download_image_guide(app).save(presentation_data)
            presentation_data.seek(0)
            return send_file(presentation_data, as_attachment=True, download_name='image-guide.pptx')
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
    url = f'{app.config.get("TATOR_URL")}/rest/GetFrame/{media_id}?frames={frame}'
    if request.values.get('preview'):
        url += '&quality=650'
    res = requests.get(
        url=url,
        headers={'Authorization': f'Token {token}'}
    )
    if res.status_code == 200:
        base64_image = base64.b64encode(res.content).decode('utf-8')
        return Response(base64.b64decode(base64_image), content_type='image/png'), 200
    return '', 500


# view tator localization image
@app.get('/tator-localization/<localization_id>')
def tator_image(localization_id):
    if not session.get('tator_token'):
        if not request.values.get('token'):
            return {}, 400
        token = request.values.get('token')
    else:
        token = session["tator_token"]
    res = requests.get(
        url=f'{app.config.get("TATOR_URL")}/rest/LocalizationGraphic/{localization_id}',
        headers={'Authorization': f'Token {token}'}
    )
    if res.status_code == 200:
        base64_image = base64.b64encode(res.content).decode('utf-8')
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
            api = tator.get_api(
                host=app.config.get('TATOR_URL'),
                token=session.get('tator_token'),
            )
            api.update_localization_by_elemental_id(
                version=localization['version'],
                elemental_id=localization['elemental_id'],
                localization_update=tator.models.LocalizationUpdate(
                    attributes=this_attributes,
                )
            )
    except tator.openapi.tator_openapi.exceptions.ApiException:
        return {}, 500
    return {}, 200


# update tator localization 'good image'
@app.patch('/tator/localization/good-image')
def update_tator_localization_image():
    localization_elemental_ids = request.values.getlist('localization_elemental_ids')
    version = request.values.get('version')
    try:
        for elemental_id in localization_elemental_ids:
            api = tator.get_api(
                host=app.config.get('TATOR_URL'),
                token=session.get('tator_token'),
            )
            api.update_localization_by_elemental_id(
                version=version,
                elemental_id=elemental_id,
                localization_update=tator.models.LocalizationUpdate(
                    attributes={
                        'Good Image': True if request.values.get('good_image') == 'true' else False,
                    },
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
                url=f'{app.config.get("DARC_REVIEW_URL")}/comment/sequence/{sequence}',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
            ) as res:
                comments = comments | res.json()  # merge dicts
            if sequence not in session.get('vars_video_sequences', []):
                return render_template('not-found.html', err='dive'), 404
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to external review server\n')
    # get images in sequence
    image_loader = VarsAnnotationProcessor(sequences)
    image_loader.process_sequences()
    if len(image_loader.final_records) < 1:
        return render_template('not-found.html', err='pics'), 404
    data = {
        'annotations': image_loader.final_records,
        'highest_id_ref': image_loader.highest_id_ref,
        'title': image_loader.vessel_name,
        'concepts': session.get('vars_concepts', []),
        'reviewers': session.get('reviewers', []),
        'comments': comments,
    }
    return render_template('image-review/image-review.html', data=data)


# qaqc checklist page
@app.get('/vars/qaqc-checklist')
def vars_qaqc_checklist():
    sequences = request.args.getlist('sequence')
    annotation_count = 0
    individual_count = 0
    true_localization_count = 0  # number of bounding box associations in dive
    group_localization_count = 0  # number of annotations marked 'group: localization'
    identity_references = set()
    with requests.get(
        url=f'{app.config.get("DARC_REVIEW_URL")}/vars-qaqc-checklist/{"&".join(request.args.getlist("sequence"))}',
        headers=app.config.get('DARC_REVIEW_HEADERS'),
    ) as checklist_res:
        if checklist_res.status_code == 200:
            checklist = checklist_res.json()
        else:
            print('ERROR: Unable to get QAQC checklist from external review server')
            checklist = {}
    # get counts
    for sequence in sequences:
        with requests.get(f'{app.config.get("HURLSTOR_URL")}:8086/query/dive/{sequence.replace(" ", "%20")}') as r:
            annotation_count += len(r.json()['annotations'])
            for annotation in r.json()['annotations']:
                if annotation['concept'][0].islower():  # ignore non-taxonomic concepts
                    continue
                if annotation.get('group') == 'localization':
                    true_localization_count += 1
                    group_localization_count += 1
                    continue
                id_ref = None
                cat_abundance = None
                pop_quantity = None
                for association in annotation['associations']:
                    if association['link_name'] == 'identity-reference':
                        id_ref = association['link_value']
                    elif association['link_name'] == 'categorical-abundance':
                        cat_abundance = association['link_value']
                    elif association['link_name'] == 'population-quantity':
                        pop_quantity = association['link_value']
                    elif association['link_name'] == 'bounding box':
                        true_localization_count += 1
                if id_ref:
                    if id_ref in identity_references:
                        continue
                    else:
                        identity_references.add(id_ref)
                if cat_abundance:
                    match cat_abundance:
                        case '11-20':
                            individual_count += 15
                        case '21-50':
                            individual_count += 35
                        case '51-100':
                            individual_count += 75
                        case '\u003e100':
                            individual_count += 100
                    continue
                if pop_quantity and pop_quantity != '':
                    individual_count += int(pop_quantity)
                    continue
                individual_count += 1
    return render_template(
        'qaqc/vars/qaqc-checklist.html',
        annotation_count=annotation_count,
        individual_count=individual_count,
        true_localization_count=true_localization_count,
        group_localization_count=group_localization_count,
        checklist=checklist,
    )


# update vars qaqc checklist
@app.patch('/vars/qaqc-checklist')
def patch_vars_qaqc_checklist():
    req_json = request.json
    sequences = req_json.get('sequences')
    if not sequences:
        return {}, 400
    req_json.pop('sequences')
    res = requests.patch(
        url=f'{app.config.get("DARC_REVIEW_URL")}/vars-qaqc-checklist/{sequences}',
        headers=app.config.get('DARC_REVIEW_HEADERS'),
        json=req_json,
    )
    return res.json(), res.status_code


# individual qaqc checks (VARS)
@app.get('/vars/qaqc/<check>')
def vars_qaqc(check):
    sequences = request.args.getlist('sequence')
    qaqc_annos = VarsQaqcProcessor(sequences)
    data = {
        'concepts': session.get('vars_concepts', []),
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
        case 'number-of-bounding-boxes':
            qaqc_annos.find_num_bounding_boxes()
            data['page_title'] = 'Number of bounding boxes for each unique concept'
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


# displays comments in the external review db
@app.get('/external-review')
def get_external_review():
    comments = []
    unread_comments = 0
    read_comments = 0
    total_comments = 0
    if 'tator_token' in session.keys():
        try:
            api = tator.get_api(
                host=app.config.get('TATOR_URL'),
                token=session['tator_token'],
            )
        except tator.openapi.tator_openapi.exceptions.ApiException:
            flash('Error connecting to Tator', 'danger')
            return redirect('/')
    try:
        print('Fetching external comments...', end='')
        sys.stdout.flush()
        with requests.get(
                url=f'{app.config.get("DARC_REVIEW_URL")}/stats',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
        ) as stats_res:
            stats_json = stats_res.json()
            unread_comments = stats_json['unread_comments']
            read_comments = stats_json['read_comments']
            total_comments = stats_json['total_comments']
        # get a list of comments from external review db
        if request.args.get('reviewer'):
            query = ''
            if request.args.get('read'):
                query += '?read=true'
            elif request.args.get('unread'):
                query += '?unread=true'
            comments_res = requests.get(
                url=f'{app.config.get("DARC_REVIEW_URL")}/comment/reviewer/{request.args.get("reviewer")}{query}',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
            )
            comments_json = comments_res.json()
            comments = comments_json['comments']
            unread_comments = comments_json['unread_comments']
            read_comments = comments_json['read_comments']
            total_comments = comments_json['total_comments']
        elif request.args.get('unread'):
            unread_comments_res = requests.get(
                url=f'{app.config.get("DARC_REVIEW_URL")}/comment/unread',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
            )
            comments = unread_comments_res.json()
        elif request.args.get('read'):
            read_comments_res = requests.get(
                url=f'{app.config.get("DARC_REVIEW_URL")}/comment/read',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
            )
            comments = read_comments_res.json()
        else:
            all_comments_res = requests.get(
                url=f'{app.config.get("DARC_REVIEW_URL")}/comment/all',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
            )
            comments = all_comments_res.json()
        print('fetched!')
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
        'concepts': session.get('vars_concepts', []),
        'reviewers': session.get('reviewers', []),
        'comments': comments,
        'missing_records': comment_loader.missing_records,
        'unread_comment_count': unread_comments,
        'read_comment_count': read_comments,
        'total_comment_count': total_comments,
    }
    return render_template('image-review/image-review.html', data=data)


# adds an annotation for review/updates the reviewer for an annotation
@app.post('/external-review')
def add_external_review():
    def add_vars_or_tator_comment(status_code):
        if not request.values.get('all_localizations'):  # VARS annotation, update VARS comment
            annosaurus = Annosaurus(app.config.get('ANNOSAURUS_URL'))
            annosaurus.update_annotation_comment(
                observation_uuid=request.values.get('observation_uuid'),
                reviewers=json.loads(request.values.get('reviewers')),
                client_secret=app.config.get('ANNOSAURUS_CLIENT_SECRET')
            )
        else:  # Tator localization, update Tator notes
            api = tator.get_api(
                host=app.config.get('TATOR_URL'),
                token=session.get('tator_token'),
            )
            current_notes = api.get_localization_by_elemental_id(
                version=json.loads(request.values.get('all_localizations'))[0].get('version', 45),
                elemental_id=request.values.get('observation_uuid'),
            ).attributes.get('Notes', '').split('|')
            current_notes = [note for note in current_notes if 'send to' not in note.lower()]  # get rid of 'send to expert' notes
            current_notes = [note for note in current_notes if 'added for review' not in note.lower()]  # get rid of old 'added for review' notes
            current_notes = '|'.join(current_notes)
            new_notes = f'{current_notes + "|" if current_notes else ""}Added for review: {", ".join(json.loads(request.values.get("reviewers")))}'
            api.update_localization_by_elemental_id(
                version=json.loads(request.values.get('all_localizations'))[0].get('version', 45),
                elemental_id=request.values.get('observation_uuid'),
                localization_update=tator.models.LocalizationUpdate(
                    attributes={'Notes': new_notes},
                )
            )
        return {}, status_code
    data = {
        'uuid': request.values.get('observation_uuid'),
        'all_localizations': request.values.get('all_localizations'),
        'id_reference': request.values.get('id_reference'),
        'section_id': request.values.get('section_id'),
        'sequence': request.values.get('sequence'),
        'timestamp': request.values.get('timestamp'),
        'reviewers': request.values.get('reviewers'),
        'image_url': request.values.get('image_url'),
        'video_url': request.values.get('video_url'),
        'annotator': request.values.get('annotator'),
        'depth': request.values.get('depth'),
        'lat': request.values.get('lat'),
        'long': request.values.get('long'),
        'temperature': request.values.get('temperature'),
        'oxygen_ml_l': request.values.get('oxygen_ml_l'),
    }
    with requests.post(
            url=f'{app.config.get("DARC_REVIEW_URL")}/comment',
            headers=app.config.get('DARC_REVIEW_HEADERS'),
            data=data,
    ) as post_comment_res:
        if post_comment_res.status_code == 409:  # comment already exists in the db, update record
            put_comment_res = requests.put(
                url=f'{app.config.get("DARC_REVIEW_URL")}/comment/reviewers/{data["uuid"]}',
                headers=app.config.get('DARC_REVIEW_HEADERS'),
                data=data,
            )
            if put_comment_res.status_code == 200:
                return add_vars_or_tator_comment(200)
        elif post_comment_res.status_code == 201:  # comment added to db, update VARS "comment" field
            return add_vars_or_tator_comment(201)
        return {}, 500


# deletes an item from the external review db
@app.delete('/external-review')
def delete_external_review():
    delete_comment_res = requests.delete(
        url=f'{app.config.get("DARC_REVIEW_URL")}/comment/{request.values.get("uuid")}',
        headers=app.config.get('DARC_REVIEW_HEADERS'),
    )
    if delete_comment_res.status_code == 200:
        if request.values.get('tator') and request.values.get('tator') == 'true':  # tator localization
            api = tator.get_api(
                host=app.config.get('TATOR_URL'),
                token=session.get('tator_token'),
            )
            current_notes = api.get_localization_by_elemental_id(
                version=request.values.get('tator_version'),
                elemental_id=request.values.get('uuid'),
            ).attributes.get('Notes', '').split('|')
            current_notes = [note for note in current_notes if 'send to' not in note.lower()]  # get rid of 'send to expert' notes
            current_notes = [note for note in current_notes if 'added for review' not in note.lower()]  # get rid of old 'added for review' notes
            api.update_localization_by_elemental_id(
                version=request.values.get('tator_version'),
                elemental_id=request.values.get('uuid'),
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


# displays information about all the reviewers in the hurl db
@app.get('/reviewers')
def reviewers():
    return render_template('external-reviewers.html', reviewers=session.get('reviewers'))


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
    patch_reviewer_res = requests.patch(
        url=f'{app.config.get("DARC_REVIEW_URL")}/reviewer/{name}',
        headers=app.config.get('DARC_REVIEW_HEADERS'),
        data=data,
    )
    if patch_reviewer_res.status_code == 404:
        data['name'] = data['new_name']
        post_reviewer_res = requests.post(
            url=f'{app.config.get("DARC_REVIEW_URL")}/reviewer',
            headers=app.config.get('DARC_REVIEW_HEADERS'),
            data=data,
        )
        if post_reviewer_res.status_code == 201:
            success = True
            flash('Successfully added reviewer', 'success')
        else:
            flash('Unable to add reviewer', 'danger')
    elif patch_reviewer_res.status_code == 200:
        success = True
        flash('Successfully updated reviewer', 'success')
    else:
        flash('Unable to update reviewer', 'danger')
    if success:
        with requests.get(
            url=f'{app.config.get("DARC_REVIEW_URL")}/reviewer/all',
            headers=app.config.get('DARC_REVIEW_HEADERS'),
        ) as all_reviewers_res:
            session['reviewers'] = all_reviewers_res.json()
    return redirect('/reviewers')


# delete a reviewer
@app.delete('/reviewer/<name>')
def delete_reviewer(name):
    delete_reviewer_res = requests.delete(
        url=f'{app.config.get("DARC_REVIEW_URL")}/reviewer/{name}',
        headers=app.config.get('DARC_REVIEW_HEADERS'),
    )
    if delete_reviewer_res.status_code == 200:
        flash('Successfully deleted reviewer', 'success')
        with requests.get(
            url=f'{app.config.get("DARC_REVIEW_URL")}/reviewer/all',
            headers=app.config.get('DARC_REVIEW_HEADERS'),
        ) as res:
            session['reviewers'] = res.json()
    else:
        flash('Error deleting reviewer', 'danger')
    return {}, delete_reviewer_res.status_code


# get an updated VARS annotation
@app.get('/current-annotation/<observation_uuid>')
def get_current_associations(observation_uuid):
    res = requests.get(url=f'{app.config.get("HURLSTOR_URL")}:8082/v1/annotations/{observation_uuid}')
    if res.status_code != 200:
        return {}, res.status_code
    return res.json(), 200


# updates annotation with new concept name
@app.patch('/vars/annotation-concept')
def update_annotation():
    annosaurus = Annosaurus(app.config.get('ANNOSAURUS_URL'))
    updated_response = annosaurus.update_concept_name(
        observation_uuid=request.values.get('observation_uuid'),
        concept=request.values.get('concept'),
        client_secret=app.config.get('ANNOSAURUS_CLIENT_SECRET'),
    )
    return updated_response['json'], updated_response['status']


# creates a new association for a VARS annotation
@app.post('/vars/association')
def create_association():
    annosaurus = Annosaurus(app.config.get('ANNOSAURUS_URL'))
    new_association = {
        'link_name': request.values.get('link_name'),
        'link_value': request.values.get('link_value'),
        'to_concept': request.values.get('to_concept'),
    }
    created_response = annosaurus.create_association(
        observation_uuid=request.values.get('observation_uuid'),
        association=new_association,
        client_secret=app.config.get('ANNOSAURUS_CLIENT_SECRET'),
    )
    if created_response['status'] == 200:
        created_response['status'] = 201
    return created_response['json'], created_response['status']


# updates a VARS association
@app.patch('/vars/association')
def update_association():
    annosaurus = Annosaurus(app.config.get('ANNOSAURUS_URL'))
    updated_association = {
        'link_name': request.values.get('link_name'),
        'link_value': request.values.get('link_value'),
        'to_concept': request.values.get('to_concept'),
    }
    updated_response = annosaurus.update_association(
        association_uuid=request.values.get('uuid'),
        association=updated_association,
        client_secret=app.config.get('ANNOSAURUS_CLIENT_SECRET'),
    )
    return updated_response['json'], updated_response['status']


# deletes a VARS association
@app.delete('/vars/association/<uuid>')
def delete_association(uuid):
    annosaurus = Annosaurus(app.config.get('ANNOSAURUS_URL'))
    deleted = annosaurus.delete_association(
        association_uuid=uuid,
        client_secret=app.config.get('ANNOSAURUS_CLIENT_SECRET'),
    )
    return deleted['json'], deleted['status']


# add a new concept to the attracted collection
@app.post('/attracted')
def add_attracted():
    res = requests.post(
        url=f'{app.config.get("DARC_REVIEW_URL")}/attracted',
        headers=app.config.get('DARC_REVIEW_HEADERS'),
        data={
            'scientific_name': request.values.get('concept'),
            'attracted': request.values.get('attracted'),
        },
    )
    if res.status_code == 201:
        flash(f'Added {request.values.get("concept")}', 'success')
    return res.json(), res.status_code


# update an existing attracted concept
@app.patch('/attracted/<concept>')
def update_attracted(concept):
    res = requests.patch(
        url=f'{app.config.get("DARC_REVIEW_URL")}/attracted/{concept}',
        headers=app.config.get('DARC_REVIEW_HEADERS'),
        data={
            'attracted': request.values.get('attracted'),
        }
    )
    if res.status_code == 200:
        flash(f'Updated {concept}', 'success')
    return res.json(), res.status_code


# delete an attracted concept
@app.delete('/attracted/<concept>')
def delete_attracted(concept):
    res = requests.delete(
        url=f'{app.config.get("DARC_REVIEW_URL")}/attracted/{concept}',
        headers=app.config.get('DARC_REVIEW_HEADERS'),
    )
    if res.status_code == 200:
        flash(f'Deleted {concept}', 'success')
    return res.json(), res.status_code


@app.errorhandler(404)
def page_not_found(e):
    return render_template('not-found.html', err=''), 404


@app.get('/video')
def video():
    data = {'link': request.args.get('link'), 'time': request.args.get('time')}
    return render_template('video.html', data=data), 200


@app.get('/attracted-list')
def attracted_list():
    res = requests.get(url=f'{app.config.get("DARC_REVIEW_URL")}/attracted')
    return render_template('qaqc/tator/attracted-list.html', attracted_concepts=res.json()), 200


@app.errorhandler(Exception)
def server_error(e):
    error = f'{type(e).__name__}: {e}'
    print('\nApplication error 😔')
    print(error)
    print(traceback.format_exc())
    return render_template('error.html', err=error), 500
