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
from ...util.tator_localization_type import TatorLocalizationType


# view QA/QC checklist for a specified project & section
@tator_qaqc_bp.get('/checklist')
def tator_qaqc_checklist():
    project_id = int(request.args.get('project'))
    section_ids = request.args.getlist('section')
    deployment_names = []
    expedition_name = None
    if not project_id or not section_ids:
        flash('Please select a project and section', 'info')
        return redirect('/')
    if 'tator_token' not in session.keys():
        flash('Please log in to Tator', 'info')
        return redirect('/')
    try:
        api = tator.get_api(
            host=current_app.config.get('TATOR_URL'),
            token=session['tator_token'],
        )
        for section_id in section_ids:
            section = api.get_section(id=int(section_id))
            deployment_names.append(section.name)
            if expedition_name is None:
                expedition_name = section.path.split('.')[0]
    except tator.openapi.tator_openapi.exceptions.ApiException:
        flash('Please log in to Tator', 'info')
        return redirect('/')
    localizations = []
    individual_count = 0
    with requests.get(
            url=f'{current_app.config.get("DARC_REVIEW_URL")}/tator-qaqc-checklist/{"&".join(deployment_names)}',
            headers=current_app.config.get('DARC_REVIEW_HEADERS'),
    ) as checklist_res:
        if checklist_res.status_code == 200:
            checklist = checklist_res.json()
        else:
            print('ERROR: Unable to get QAQC checklist from external review server')
            checklist = {}
    # REST is much faster than Python API for large queries
    for section_id in section_ids:
        res = requests.get(
            url=f'{current_app.config.get("TATOR_URL")}/rest/Localizations/{project_id}?section={section_id}',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Token {session["tator_token"]}',
            })
        localizations += res.json()
    for localization in localizations:
        if localization['type'] == TatorLocalizationType.DOT.value:
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
        'title': expedition_name,
        'tab_title': deployment_names[0] if len(deployment_names) == 1 else expedition_name,
        'deployments': ', '.join(deployment_names),
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
    project_id = int(request.args.get('project'))
    section_ids = request.args.getlist('section')
    deployment_names = []
    expedition_name = None
    if not project_id or not section_ids:
        flash('Please select a project and section', 'info')
        return redirect('/')
    if 'tator_token' not in session.keys():
        flash('Please log in to Tator', 'info')
        return redirect('/')
    try:
        api = tator.get_api(
            host=current_app.config.get('TATOR_URL'),
            token=session['tator_token'],
        )
        for section_id in section_ids:
            section = api.get_section(id=int(section_id))
            deployment_names.append(section.name)
            if expedition_name is None:
                expedition_name = section.path.split('.')[0]
    except tator.openapi.tator_openapi.exceptions.ApiException:
        flash('Please log in to Tator', 'info')
        return redirect('/')
    # get comments and image references from external review db
    comments = {}
    image_refs = {}
    try:
        for deployment in deployment_names:
            comment_res = requests.get(
                    url=f'{current_app.config.get("DARC_REVIEW_URL")}/comment/sequence/{deployment}',
                    headers=current_app.config.get('DARC_REVIEW_HEADERS'),
            )
            if comment_res.status_code != 200:
                raise requests.exceptions.ConnectionError
            comments |= comment_res.json()  # merge dicts
        image_ref_res = requests.get(f'{current_app.config.get("DARC_REVIEW_URL")}/image-reference/quick')
        if image_ref_res.status_code != 200:
            raise requests.exceptions.ConnectionError
        image_refs = image_ref_res.json()
    except requests.exceptions.ConnectionError:
        print('\nERROR: unable to connect to external review server\n')
    tab_title = deployment_names[0] if len(deployment_names) == 1 else expedition_name
    data = {
        'concepts': session.get('vars_concepts', []),
        'title': check.replace('-', ' ').title(),
        'tab_title': f'{tab_title} {check.replace("-", " ").title()}',
        'reviewers': session.get('reviewers', []),
        'comments': comments,
        'image_refs': image_refs,
    }
    if check == 'media-attributes':
        # the one case where we don't want to initialize a TatorQaqcProcessor (no need to fetch localizations)
        media_attributes = {}
        for section_id in section_ids:
            media_attributes[section_id] = []
            res = requests.get(  # REST API is much faster than Python API for large queries
                url=f'{current_app.config.get("TATOR_URL")}/rest/Medias/{project_id}?section={section_id}',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Token {session["tator_token"]}',
                })
            if res.status_code != 200:
                raise tator.openapi.tator_openapi.exceptions.ApiException
            for media in res.json():
                media_attributes[section_id].append(media)
        data['page_title'] = 'Media attributes'
        data['media_attributes'] = media_attributes
        return render_template('qaqc/tator/qaqc-tables.html', data=data)
    qaqc_annos = TatorQaqcProcessor(
        project_id=project_id,
        section_ids=section_ids,
        api=api,
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
        case 'exists-in-image-references':
            qaqc_annos.check_exists_in_image_references(image_refs)
            data['page_title'] = 'Records that do not exist in image references'
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
    else:
        flash(f'Failed to add {request.values.get("concept")}', 'danger')
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
