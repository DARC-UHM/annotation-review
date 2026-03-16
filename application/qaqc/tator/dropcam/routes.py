"""
Dropcam (dscm) QA/QC endpoints

/qaqc/tator/dropcam/checklist [GET, PATCH]
/qaqc/tator/dropcam/check/<check> [GET]
/qaqc/tator/dropcam/attracted-list [GET]
/qaqc/tator/dropcam/attracted [POST]
/qaqc/tator/dropcam/attracted/<concept> [PATCH, DELETE]
"""
from io import BytesIO

import requests
from flask import current_app, flash, redirect, render_template, request, send_file, session

from . import dropcam_qaqc_bp
from application.tator.tator_dropcam_qaqc_processor import TatorDropcamQaqcProcessor
from application.tator.tator_type import TatorLocalizationType
from application.tator.tator_rest_client import TatorRestClient
from application.qaqc.tator.util import init_tator_api, get_comments_and_image_refs


def _get_deployment_info(tator_api, section_ids):
    deployment_names = []
    expedition_name = None
    for section_id in section_ids:
        section = tator_api.get_section(id=int(section_id))
        deployment_names.append(section.name)
        if expedition_name is None:
            expedition_name = section.path.split('.')[0]
    return deployment_names, expedition_name


# view QA/QC checklist for a specified project & section
@dropcam_qaqc_bp.get('/checklist')
def dropcam_qaqc_checklist():
    project_id = int(request.args.get('project'))
    section_ids = request.args.getlist('section')
    if not project_id or not section_ids:
        flash('Please select a project and section', 'info')
        return redirect('/')
    tator_api, err = init_tator_api()
    if err:
        return err
    deployment_names, expedition_name = _get_deployment_info(tator_api, section_ids)
    tator_client = TatorRestClient(current_app.config.get('TATOR_URL'), session['tator_token'])
    localizations = []
    individual_count = 0
    with requests.get(
            url=f'{current_app.config.get("DARC_REVIEW_URL")}/qaqc-checklist/tator-dropcam/{"&".join(deployment_names)}',
            headers=current_app.config.get('DARC_REVIEW_HEADERS'),
    ) as checklist_res:
        if checklist_res.status_code == 200:
            checklist = checklist_res.json()
        else:
            print('ERROR: Unable to get QAQC checklist from external review server')
            checklist = {}
    for section_id in section_ids:
        localizations += tator_client.get_localizations(project_id, section=section_id)
    for localization in localizations:
        if TatorLocalizationType.is_dot(localization['type']):
            individual_count += 1
            if localization['attributes'].get('Categorical Abundance', '--') != '--':
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
        'deployment_names': deployment_names,
        'localization_count': len(localizations),
        'individual_count': individual_count,
        'checklist': checklist,
    }
    return render_template('qaqc/tator/dropcam/qaqc-checklist.html', data=data)


# update tator qaqc checklist
@dropcam_qaqc_bp.patch('/checklist')
def patch_dropcam_qaqc_checklist():
    req_json = request.json
    deployments = req_json.get('deployments')
    if not deployments:
        return {}, 400
    req_json.pop('deployments')
    res = requests.patch(
        url=f'{current_app.config.get("DARC_REVIEW_URL")}/qaqc-checklist/tator-dropcam/{deployments}',
        headers=current_app.config.get('DARC_REVIEW_HEADERS'),
        json=req_json,
    )
    return res.json(), res.status_code


# individual qaqc checks
@dropcam_qaqc_bp.get('/check/<check>')
def dropcam_qaqc(check):
    project_id = int(request.args.get('project'))
    section_ids = request.args.getlist('section')
    if not project_id or not section_ids:
        flash('Please select a project and section', 'info')
        return redirect('/')
    tator_api, err = init_tator_api()
    if err:
        return err
    deployment_names, expedition_name = _get_deployment_info(tator_api, section_ids)
    tator_client = TatorRestClient(current_app.config.get('TATOR_URL'), session['tator_token'])
    comments, image_refs = get_comments_and_image_refs(deployment_names)
    tab_title = deployment_names[0] if len(deployment_names) == 1 else expedition_name
    data = {
        'concepts': session.get('vars_concepts', []),
        'title': check.replace('-', ' ').title(),
        'tab_title': f'{tab_title} {check.replace("-", " ").title()}',
        'deployment_names': deployment_names,
        'reviewers': session.get('reviewers', []),
        'comments': comments,
        'image_refs': image_refs,
        'qaqc_js': 'qaqc.tator_qaqc.dropcam_qaqc.static',
    }
    if check == 'media-attributes':
        # the one case where we don't want to initialize a TatorDropcamQaqcProcessor (no need to fetch localizations)
        media_attributes = {}
        for section_id in section_ids:
            media_attributes[section_id] = tator_client.get_medias(project_id, section=section_id)
        data['page_title'] = 'Media attributes'
        data['media_attributes'] = media_attributes
        return render_template('qaqc/tator/qaqc-tables.html', data=data)
    qaqc_annos = TatorDropcamQaqcProcessor(
        project_id=project_id,
        section_ids=section_ids,
        api=tator_api,
        darc_review_url=current_app.config.get('DARC_REVIEW_URL'),
        tator_url=current_app.config.get('TATOR_URL'),
    )
    qaqc_annos.fetch_localizations()
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
            data['subtitle'] = '(also flags records with taxa that can be either)'
            data['attracted_concepts'] = attracted_concepts
        case 'exists-in-image-references':
            qaqc_annos.check_exists_in_image_references(image_refs)
            data['page_title'] = 'Records that do not exist in image references'
            data['subtitle'] = '(also flags records that have both a tentative ID and a morphospecies)'
        case 'same-name-qualifier':
            qaqc_annos.check_same_name_qualifier()
            data['page_title'] = 'Records with the same scientific name/tentative ID but different qualifiers'
        case 'non-target-not-attracted':
            qaqc_annos.check_non_target_not_attracted()
            data['page_title'] = '"Non-target" records marked as "attracted"'
        case 'all-tentative-ids':
            qaqc_annos.get_all_tentative_ids_and_morphospecies()
            data['page_title'] = 'Records with a tentative ID or morphospecies'
            data['subtitle'] = '(also checks phylogeny vs. scientific name)'
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
@dropcam_qaqc_bp.get('/attracted-list')
def attracted_list():
    res = requests.get(url=f'{current_app.config.get("DARC_REVIEW_URL")}/attracted')
    return render_template('qaqc/tator/dropcam/attracted-list.html', attracted_concepts=res.json()), 200


# add a new concept to the attracted collection
@dropcam_qaqc_bp.post('/attracted')
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
@dropcam_qaqc_bp.patch('/attracted/<concept>')
def update_attracted(concept):
    res = requests.patch(
        url=f'{current_app.config.get("DARC_REVIEW_URL")}/attracted/{concept}',
        headers=current_app.config.get('DARC_REVIEW_HEADERS'),
        data={'attracted': request.values.get('attracted')},
    )
    if res.status_code == 200:
        flash(f'Updated {concept}', 'success')
    return res.json(), res.status_code


# delete an attracted concept
@dropcam_qaqc_bp.delete('/attracted/<concept>')
def delete_attracted(concept):
    res = requests.delete(
        url=f'{current_app.config.get("DARC_REVIEW_URL")}/attracted/{concept}',
        headers=current_app.config.get('DARC_REVIEW_HEADERS'),
    )
    if res.status_code == 200:
        flash(f'Deleted {concept}', 'success')
    return res.json(), res.status_code
