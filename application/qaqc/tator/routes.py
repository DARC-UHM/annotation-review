"""
Tator-specific QA/QC endpoints

/qaqc/tator/checklist [GET, PATCH]
/qaqc/tator/check/<check> [GET]
/qaqc/tator/attracted-list [GET]
/qaqc/tator/attracted [POST]
/qaqc/tator/attracted/<concept> [PATCH, DELETE]
"""

from io import BytesIO

import tator
import requests
from flask import current_app, flash, redirect, render_template, request, send_file, session

from . import tator_qaqc_bp
from .tator_qaqc_processor import TatorQaqcProcessor


# view QA/QC checklist for a specified project & section
@tator_qaqc_bp.get('/checklist')
def tator_qaqc_checklist():
    if not request.args.get('project') or not request.args.get('section') or not request.args.getlist('deployment'):
        flash('Please select a project, section, and deployment', 'info')
        return redirect('/')
    project_id = int(request.args.get('project'))
    section_id = int(request.args.get('section'))
    if 'tator_token' not in session.keys():
        flash('Please log in to Tator', 'info')
        return redirect('/')
    try:
        api = tator.get_api(
            host=current_app.config.get('TATOR_URL'),
            token=session['tator_token'],
        )
        section_name = api.get_section(id=section_id).name
    except tator.openapi.tator_openapi.exceptions.ApiException:
        flash('Please log in to Tator', 'info')
        return redirect('/')
    media_ids = []
    localizations = []
    individual_count = 0
    deployments = request.args.getlist('deployment')
    for deployment in deployments:
        media_ids += session[f'{project_id}_{section_id}'][deployment]
    with requests.get(
            url=f'{current_app.config.get("DARC_REVIEW_URL")}/tator-qaqc-checklist/{"&".join(request.args.getlist("deployment"))}',
            headers=current_app.config.get('DARC_REVIEW_HEADERS'),
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
            url=f'{current_app.config.get("TATOR_URL")}/rest/Localizations/{project_id}?media_id={",".join(map(str, chunk))}',
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
        'tab_title': deployments[0] if len(deployments) == 1 else f'{deployments[0]} - {deployments[-1].split("_")[-1]}',
        'localization_count': len(localizations),
        'individual_count': individual_count,
        'checklist': checklist,
    }
    return render_template('qaqc/tator/qaqc-checklist.html', data=data)


# update tator qaqc checklist
@tator_qaqc_bp.patch('/checklist')
def patch_tator_qaqc_checklist():
    req_json = request.json
    deployments = req_json.get('deployments')
    if not deployments:
        return {}, 400
    req_json.pop('deployments')
    res = requests.patch(
        url=f'{current_app.config.get("DARC_REVIEW_URL")}/tator-qaqc-checklist/{deployments}',
        headers=current_app.config.get('DARC_REVIEW_HEADERS'),
        json=req_json,
    )
    return res.json(), res.status_code


# individual qaqc checks
@tator_qaqc_bp.get('/check/<check>')
def tator_qaqc(check):
    if 'tator_token' not in session.keys():
        flash('Please log in to Tator', 'info')
        return redirect('/')
    try:
        api = tator.get_api(
            host=current_app.config.get('TATOR_URL'),
            token=session['tator_token'],
        )
    except tator.openapi.tator_openapi.exceptions.ApiException:
        flash('Please log in to Tator', 'info')
        return redirect('/')
    # get comments from external review db
    comments = {}
    if not request.args.get('project') or not request.args.get('section') or not request.args.getlist('deployment'):
        flash('Please select a project, section, and deployment', 'info')
        return redirect('/')
    project_id = int(request.args.get('project'))
    section_id = int(request.args.get('section'))
    deployments = request.args.getlist('deployment')
    try:
        for deployment in deployments:
            with requests.get(
                    url=f'{current_app.config.get("DARC_REVIEW_URL")}/comment/sequence/{deployment}',
                    headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            ) as res:
                comments = comments | res.json()  # merge dicts
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to external review server\n')
    tab_title = deployments[0] if len(deployments) == 1 else f'{deployments[0]} - {deployments[-1].split("_")[-1]}'
    data = {
        'concepts': session.get('vars_concepts', []),
        'title': check.replace('-', ' ').title(),
        'tab_title': f'{tab_title} {check.replace("-", " ").title()}',
        'comments': comments,
        'reviewers': session.get('reviewers', []),
    }
    if check == 'media-attributes':
        # the one case where we don't want to initialize a TatorQaqcProcessor (no need to fetch localizations)
        media_attributes = {}
        for deployment in request.args.getlist('deployment'):
            media_attributes[deployment] = []
            res = requests.get(  # REST API is much faster than Python API for large queries
                url=f'{current_app.config.get("TATOR_URL")}/rest/Medias/{project_id}?section={section_id}&attribute_contains=%24name%3A%3A{deployment}',
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
        darc_review_url=current_app.config.get('DARC_REVIEW_URL'),
        tator_url=current_app.config.get('TATOR_URL'),
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
            attracted_concepts = requests.get(url=f'{current_app.config.get("DARC_REVIEW_URL")}/attracted').json()
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
            qaqc_annos.download_image_guide(current_app).save(presentation_data)
            presentation_data.seek(0)
            return send_file(presentation_data, as_attachment=True, download_name='image-guide.pptx')
        case _:
            return render_template('errors/404.html', err=''), 404
    data['annotations'] = qaqc_annos.final_records
    return render_template('qaqc/tator/qaqc.html', data=data)


# view list of saved attracted/non-attracted taxa
@tator_qaqc_bp.get('/attracted-list')
def attracted_list():
    res = requests.get(url=f'{current_app.config.get("DARC_REVIEW_URL")}/attracted')
    return render_template('qaqc/tator/attracted-list.html', attracted_concepts=res.json()), 200


# add a new concept to the attracted collection
@tator_qaqc_bp.post('/attracted')
def add_attracted():
    res = requests.post(
        url=f'{current_app.config.get("DARC_REVIEW_URL")}/attracted',
        headers=current_app.config.get('DARC_REVIEW_HEADERS'),
        data={
            'scientific_name': request.values.get('concept'),
            'attracted': request.values.get('attracted'),
        },
    )
    if res.status_code == 201:
        flash(f'Added {request.values.get("concept")}', 'success')
    return res.json(), res.status_code


# update an existing attracted concept
@tator_qaqc_bp.patch('/attracted/<concept>')
def update_attracted(concept):
    res = requests.patch(
        url=f'{current_app.config.get("DARC_REVIEW_URL")}/attracted/{concept}',
        headers=current_app.config.get('DARC_REVIEW_HEADERS'),
        data={
            'attracted': request.values.get('attracted'),
        }
    )
    if res.status_code == 200:
        flash(f'Updated {concept}', 'success')
    return res.json(), res.status_code


# delete an attracted concept
@tator_qaqc_bp.delete('/attracted/<concept>')
def delete_attracted(concept):
    res = requests.delete(
        url=f'{current_app.config.get("DARC_REVIEW_URL")}/attracted/{concept}',
        headers=current_app.config.get('DARC_REVIEW_HEADERS'),
    )
    if res.status_code == 200:
        flash(f'Deleted {concept}', 'success')
    return res.json(), res.status_code
