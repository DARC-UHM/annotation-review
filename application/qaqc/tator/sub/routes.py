"""
Sub exploratory/transect QA/QC endpoints

/qaqc/tator/sub/checklist [GET, PATCH]
/qaqc/tator/sub/check/<check> [GET]
"""
from io import BytesIO

import requests
from flask import current_app, flash, redirect, render_template, request, session, send_file

from application.tator.tator_sub_qaqc_processor import TatorSubQaqcProcessor
from . import sub_qaqc_bp
from application.tator.tator_rest_client import TatorRestClient
from application.tator.tator_type import TatorLocalizationType
from application.qaqc.tator.util import init_tator_api, get_comments_and_image_refs


def _get_deployment_info(tator_client: TatorRestClient, project_id: int, section_ids: list[str], media_ids: list[str] = None):
    deployment_names = []
    expedition_name = None
    is_transect = False
    for section_id in section_ids:
        section = tator_client.get_section_by_id(int(section_id))
        deployment_names.append(section['name'])
        if expedition_name is None:
            expedition_name = section['path'].split('.')[0]
        if 'transect' in section['path'].lower():
            is_transect = True
    if media_ids:
        media = [tator_client.get_media_by_id(int(media_id)) for media_id in media_ids]
    else:
        media = tator_client.get_medias_for_sections(project_id, [int(section_id) for section_id in section_ids])
    return media, deployment_names, expedition_name, is_transect


@sub_qaqc_bp.get('/checklist')
def sub_qaqc_checklist():
    project_id = request.args.get('project', type=int)
    section_ids = request.args.getlist('section')
    if not project_id or not section_ids:
        flash('Please select a project and section', 'info')
        return redirect('/')
    media_ids = request.args.getlist('media_id')
    tator_client = TatorRestClient(current_app.config.get('TATOR_URL'), session['tator_token'])
    media_list, deployment_names, expedition_name, is_transect = _get_deployment_info(
        tator_client=tator_client,
        project_id=project_id,
        section_ids=section_ids,
        media_ids=media_ids,
    )
    localizations = []
    if media_ids:
        deployment_list = [media['name'] for media in media_list]
        media_ids_for_fetch = [media['id'] for media in media_list]
        for i in range(0, len(media_ids_for_fetch), 50):
            localizations += tator_client.get_localizations(project_id, media_ids=media_ids_for_fetch[i:i + 50])
    else:
        deployment_list = deployment_names
        for section_id in section_ids:
            localizations += tator_client.get_localizations(project_id, section_id=int(section_id))
    individual_count = 0
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
    with requests.get(
            url=f'{current_app.config.get("DARC_REVIEW_URL")}/qaqc-checklist/tator-sub/{"&".join(media_ids or section_ids)}',
            headers=current_app.config.get('DARC_REVIEW_HEADERS'),
    ) as checklist_res:
        if checklist_res.status_code == 200:
            checklist = checklist_res.json()
        else:
            print('ERROR: Unable to get QAQC checklist from external review server')
            checklist = {}
    title_suffix = f' ({"transect" if is_transect else "exploratory"})'
    data = {
        'title': expedition_name + title_suffix,
        'tab_title': (deployment_list[0] if len(deployment_list) == 1 else expedition_name) + title_suffix,
        'deployment_list': deployment_list,
        'localization_count': len(localizations),
        'individual_count': individual_count,
        'checklist': checklist,
    }
    return render_template('qaqc/tator/sub/qaqc-checklist.html', data=data)


@sub_qaqc_bp.patch('/checklist')
def patch_sub_qaqc_checklist():
    req_json = request.json
    section_ids = req_json.get('sectionIds')
    media_ids = req_json.get('mediaIds')
    if not section_ids and not media_ids:
        return {'error': 'Section IDs or media IDs are required'}, 400
    req_json.pop('sectionIds')
    req_json.pop('mediaIds')
    res = requests.patch(
        url=f'{current_app.config.get("DARC_REVIEW_URL")}/qaqc-checklist/tator-sub/{media_ids or section_ids}',
        headers=current_app.config.get('DARC_REVIEW_HEADERS'),
        json=req_json,
    )
    return res.json(), res.status_code

# individual qaqc checks
@sub_qaqc_bp.get('/check/<check>')
def sub_qaqc(check):
    project_id = request.args.get('project', type=int)
    section_ids = request.args.getlist('section')
    media_ids = request.args.getlist('media_id')
    if not project_id or not section_ids:
        flash('Please select a project and section', 'info')
        return redirect('/')
    tator_api, err = init_tator_api()
    if err:
        return err
    tator_client = TatorRestClient(current_app.config.get('TATOR_URL'), session['tator_token'])
    media_list, deployment_names, expedition_name, is_transect = _get_deployment_info(
        tator_client=tator_client,
        project_id=project_id,
        section_ids=section_ids,
        media_ids=media_ids,
    )
    comments = None
    image_refs = None
    if check not in ['unique-taxa', 'sizes', 'image-guide']:
        comments, image_refs = get_comments_and_image_refs(deployment_names)
    media_names = [media['name'] for media in media_list] if media_ids else deployment_names
    tab_title = media_names[0] if len(media_names) == 1 else expedition_name
    title_suffix = f' ({"transect" if is_transect else "exploratory"})'
    data = {
        'concepts': session.get('vars_concepts', []),
        'title': check.replace('-', ' ').title() + title_suffix,
        'tab_title': f'{tab_title} {check.replace("-", " ").title()}{title_suffix}',
        'media_names': media_names,
        'reviewers': session.get('reviewers', []),
        'comments': comments,
        'image_refs': image_refs,
        'qaqc_js': 'qaqc.tator_qaqc.sub_qaqc.static',
    }
    if check == 'media-attributes':
        # the one case where we don't want to initialize a TatorSubQaqcProcessor (no need to fetch localizations)
        data['substrates'] = tator_client.get_substrates(
            project_id=project_id,
            section_ids=[int(section_id) for section_id in section_ids],
            media_list=media_list if media_ids else None,
        )
        data['page_title'] = 'Media attributes'
        data['media_attributes'] = media_list
        return render_template('qaqc/tator/qaqc-tables.html', data=data)
    qaqc_annos = TatorSubQaqcProcessor(
        project_id=project_id,
        section_ids=section_ids,
        media_list=media_list if media_ids else None,
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
        case 'missing-ancillary-data':
            qaqc_annos.check_missing_ancillary_data()
            data['page_title'] = 'Records missing ancillary data'
        case 'missing-upon':
            qaqc_annos.check_missing_upon_and_not_fish()
            data['page_title'] = 'Records missing upon and not a fish'
        case 'upon-not-substrate':
            qaqc_annos.check_upons_are_current_substrate_or_previous_animal()
            data['page_title'] = 'Records where upon is not the current substrate or an animal that was previously recorded'
        case 'suspicious-hosts':
            qaqc_annos.get_suspicious_records()
            data['page_title'] = 'Records with a suspicious upon (host upon itself)'
        case 'host-associate-time-diff':
            qaqc_annos.find_long_host_associate_time_diff()
            data['page_title'] = 'Records where host recorded more than one minute ago or cannot be found'
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
        case 'sizes':
            qaqc_annos.get_all_sizes()
            data['page_title'] = 'All unique taxa sizes'
            data['sizes'] = qaqc_annos.final_records
            return render_template('qaqc/tator/qaqc-tables.html', data=data)
        case 'unique-taxa':
            qaqc_annos.get_unique_taxa()
            data['page_title'] = 'All unique taxa and counts'
            data['unique_taxa'] = qaqc_annos.final_records
            return render_template('qaqc/tator/qaqc-tables.html', data=data)
        case 'summary':
            qaqc_annos.get_summary()
            data['page_title'] = 'Summary'
            data['annotations'] = qaqc_annos.final_records
            data['media_id_names'] = {media['id']: media['name'] for media in media_list}
            return render_template('qaqc/tator/qaqc-tables.html', data=data)
        case 'image-guide':
            presentation_data = BytesIO()
            qaqc_annos.download_image_guide().save(presentation_data)
            presentation_data.seek(0)
            return send_file(presentation_data, as_attachment=True, download_name=f'{tab_title} Sub Image Guide.pptx')
        case _:
            return render_template('errors/404.html', err=''), 404
    data['annotations'] = qaqc_annos.final_records
    return render_template('qaqc/tator/qaqc.html', data=data)