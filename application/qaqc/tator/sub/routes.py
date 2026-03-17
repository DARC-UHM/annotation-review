"""
Sub/transect QA/QC endpoints

/qaqc/tator/sub/checklist [GET, PATCH]
/qaqc/tator/sub/check/<check> [GET]
"""
import requests
from flask import current_app, flash, redirect, render_template, request, session

from application.tator.tator_sub_qaqc_processor import TatorSubQaqcProcessor
from . import sub_qaqc_bp
from application.tator.tator_rest_client import TatorRestClient
from application.tator.tator_type import TatorLocalizationType
from application.qaqc.tator.util import init_tator_api, get_comments_and_image_refs


def _get_deployment_info(tator_client: TatorRestClient, section_ids: list[str], transect_ids: list[str]):
    deployment_names = []
    expedition_name = None
    for section_id in section_ids:
        section = tator_client.get_section_by_id(section_id)
        deployment_names.append(section['name'])
        if expedition_name is None:
            expedition_name = section['path'].split('.')[0]
    transect_media = [tator_client.get_media_by_id(transect_id) for transect_id in transect_ids]
    return transect_media, deployment_names, expedition_name


@sub_qaqc_bp.get('/checklist')
def sub_qaqc_checklist():
    project_id = request.args.get('project', type=int)
    section_ids = request.args.getlist('section')
    transect_ids = request.args.getlist('transect')
    if not project_id or not section_ids or not transect_ids:
        flash('Please select a project, section, and transect', 'info')
        return redirect('/')
    tator_client = TatorRestClient(current_app.config.get('TATOR_URL'), session['tator_token'])
    transect_media, _, expedition_name = _get_deployment_info(
        tator_client=tator_client,
        section_ids=section_ids,
        transect_ids=transect_ids,
    )
    media_names = [media['name'] for media in transect_media]
    localizations = []
    for i in range(0, len(transect_ids), 300):
        batch = [int(tid) for tid in transect_ids[i:i + 50]]
        localizations += tator_client.get_localizations(project_id, media_id=batch)
    individual_count = sum(1 for loco in localizations if TatorLocalizationType.is_dot(loco['type']))
    with requests.get(
            url=f'{current_app.config.get("DARC_REVIEW_URL")}/qaqc-checklist/tator-sub/{"&".join(transect_ids)}',
            headers=current_app.config.get('DARC_REVIEW_HEADERS'),
    ) as checklist_res:
        if checklist_res.status_code == 200:
            checklist = checklist_res.json()
        else:
            print('ERROR: Unable to get QAQC checklist from external review server')
            checklist = {}
    data = {
        'title': expedition_name,
        'tab_title': media_names[0] if len(media_names) == 1 else expedition_name,
        'media_names': media_names,
        'transect_ids': transect_ids,
        'localization_count': len(localizations),
        'individual_count': individual_count,
        'checklist': checklist,
    }
    return render_template('qaqc/tator/sub/qaqc-checklist.html', data=data)


@sub_qaqc_bp.patch('/checklist')
def patch_sub_qaqc_checklist():
    req_json = request.json
    transects = req_json.get('transectIds')
    if not transects:
        return {'error': 'transectIds is required'}, 400
    req_json.pop('transectIds')
    res = requests.patch(
        url=f'{current_app.config.get("DARC_REVIEW_URL")}/qaqc-checklist/tator-sub/{transects}',
        headers=current_app.config.get('DARC_REVIEW_HEADERS'),
        json=req_json,
    )
    return res.json(), res.status_code

# individual qaqc checks
@sub_qaqc_bp.get('/check/<check>')
def sub_qaqc(check):
    project_id = request.args.get('project', type=int)
    section_ids = request.args.getlist('section')
    transect_ids = request.args.getlist('transect')
    if not project_id or not section_ids or not transect_ids:
        flash('Please select a project, section, and transect', 'info')
        return redirect('/')
    tator_api, err = init_tator_api()
    if err:
        return err
    tator_client = TatorRestClient(current_app.config.get('TATOR_URL'), session['tator_token'])
    transect_media, deployment_names, expedition_name = _get_deployment_info(
        tator_client=tator_client,
        section_ids=section_ids,
        transect_ids=transect_ids,
    )
    media_names = [media['name'] for media in transect_media]
    comments, image_refs = get_comments_and_image_refs(deployment_names)
    tab_title = media_names[0] if len(media_names) == 1 else expedition_name
    data = {
        'concepts': session.get('vars_concepts', []),
        'title': check.replace('-', ' ').title(),
        'tab_title': f'{tab_title} {check.replace("-", " ").title()}',
        'media_names': media_names,
        'transect_ids': transect_ids,
        'reviewers': session.get('reviewers', []),
        'comments': comments,
        'image_refs': image_refs,
        'qaqc_js': 'qaqc.tator_qaqc.sub_qaqc.static',
    }
    if check == 'media-attributes':
        # the one case where we don't want to initialize a TatorSubQaqcProcessor (no need to fetch localizations)
        data['substrates'] = tator_client.get_substrates_for_medias(project_id, transect_ids, transect_media)
        data['page_title'] = 'Media attributes'
        data['media_attributes'] = transect_media
        return render_template('qaqc/tator/qaqc-tables.html', data=data)
    qaqc_annos = TatorSubQaqcProcessor(
        project_id=project_id,
        section_ids=section_ids,
        transect_media_ids=[int(transect_id) for transect_id in transect_ids],
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

        case _:
            return render_template('errors/404.html', err=''), 404
    data['annotations'] = qaqc_annos.final_records
    return render_template('qaqc/tator/qaqc.html', data=data)