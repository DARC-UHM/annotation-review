"""
Sub/transect QA/QC endpoints

/qaqc/tator/sub/checklist [GET, PATCH]
TODO /qaqc/tator/dropcam/check/<check> [GET]
"""
import json

import tator
import requests
from flask import current_app, flash, redirect, render_template, request, session

from . import sub_qaqc_bp
from application.tator.tator_rest_client import TatorRestClient
from application.tator.tator_type import TatorLocalizationType


@sub_qaqc_bp.get('/checklist')
def sub_qaqc_checklist():
    project_id = request.args.get('project', type=int)
    section_ids = request.args.getlist('section')
    transect_ids = request.args.getlist('transect')
    if not project_id or not section_ids or not transect_ids:
        flash('Please select a project, section, and transect', 'info')
        return redirect('/')
    if 'tator_token' not in session.keys():
        flash('Please log in to Tator', 'info')
        return redirect('/')
    try:
        tator_api = tator.get_api(
            host=current_app.config.get('TATOR_URL'),
            token=session['tator_token'],
        )
    except tator.openapi.tator_openapi.exceptions.ApiException as e:
        flash(json.loads(e.body)['message'], 'danger')
        return redirect('/')
    expedition_name = tator_api.get_section(section_ids[0]).path.split('.')[0]
    transect_media = tator_api.get_media_list(project_id, media_id=[int(tid) for tid in transect_ids])
    media_names = [media.name for media in transect_media]
    localizations = []
    tator_client = TatorRestClient(current_app.config.get('TATOR_URL'), session['tator_token'])
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
