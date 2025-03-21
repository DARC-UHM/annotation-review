"""
General endpoints for Tator that are used throughout the application.

/tator/login [POST]
/tator/token [GET]
/tator/logout [GET]
/tator/projects [GET]
/tator/sections/<project_id> [GET]
/tator/deployments/<project_id>/<section_id> [GET]
/tator/refresh-sections [GET]
/tator/frame/<media_id>/<frame> [GET]
/tator/localization-image/<localization_id> [GET]
/tator/localization [PATCH]
/tator/localization/good-image [PATCH]
"""

import base64
import json

import tator
import requests
from flask import current_app, request, session, Response

from . import tator_bp


# log in to tator (get token from tator)
@tator_bp.post('/login')
def tator_login():
    res = requests.post(
        url=f'{current_app.config.get("TATOR_URL")}/rest/Token',
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
@tator_bp.get('/token')
def check_tator_token():
    if 'tator_token' not in session.keys():
        return {}, 400
    try:
        api = tator.get_api(
            host=current_app.config.get('TATOR_URL'),
            token=session['tator_token'],
        )
        print(f'Your Tator token: {session["tator_token"]}')
        return {'username': api.whoami().username}, 200
    except tator.openapi.tator_openapi.exceptions.ApiException:
        return {}, 400


# clears stored tator token
@tator_bp.get('/logout')
def tator_logout():
    session.pop('tator_token', None)
    return {}, 200


# get a list of projects associated with user from tator
@tator_bp.get('/projects')
def tator_projects():
    try:
        project_list = tator.get_api(
            host=current_app.config.get('TATOR_URL'),
            token=session.get('tator_token'),
        ).get_project_list()
        return [{'id': project.id, 'name': project.name} for project in project_list], 200
    except tator.openapi.tator_openapi.exceptions.ApiException:
        return {}, 400


# get a list of sections associated with a project from tator
@tator_bp.get('/sections/<project_id>')
def tator_sections(project_id):
    try:
        section_list = tator.get_api(
            host=current_app.config.get('TATOR_URL'),
            token=session.get('tator_token'),
        ).get_section_list(project_id)
        return [{'id': section.id, 'name': section.name} for section in section_list], 200
    except tator.openapi.tator_openapi.exceptions.ApiException:
        return {}, 400


# get a list of deployments associated with a project & section from tator
@tator_bp.get('/deployments/<project_id>/<section_id>')
def load_media(project_id, section_id):
    if f'{project_id}_{section_id}' in session.keys() and request.args.get('refresh') != 'true':
        return sorted(session[f'{project_id}_{section_id}'].keys()), 200
    else:
        deployment_list = {}
        # REST is much faster than Python API for large queries
        res = requests.get(
            url=f'{current_app.config.get("TATOR_URL")}/rest/Medias/{project_id}?section={section_id}',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Token {session.get("tator_token")}',
            })
        if res.status_code != 200:
            return {}, res.status_code
        for media in res.json():
            media_name_parts = media['name'].split('_')
            # stupid solution until we decide on an actual naming convention...never?
            if 'dscm' in media_name_parts and media_name_parts.index('dscm') == 2:  # format SLB_2024_dscm_01_C001.MP4
                deployment_name = '_'.join(media_name_parts[0:4])
            elif 'dscm' in media_name_parts and media_name_parts.index('dscm') == 1:  # format HAW_dscm_01_c010_202304250123Z_0983m.mp4
                deployment_name = '_'.join(media_name_parts[0:3])
            else:  # format DOEX0087_NIU-dscm-02_c009.mp4
                deployment_name = media_name_parts[1]
            if deployment_name not in deployment_list.keys():
                deployment_list[deployment_name] = [media['id']]
            else:
                deployment_list[deployment_name].append(media['id'])
        session[f'{project_id}_{section_id}'] = deployment_list
        return sorted(deployment_list.keys()), 200


# deletes stored tator sections
@tator_bp.get('/refresh-sections')
def refresh_tator_sections():
    for key in list(session.keys()):
        if key.split('_')[0] == '26':  # id for NGS-ExTech Project
            session.pop(key)
    return {}, 200


# view tator video frame (not cropped)
@tator_bp.get('/frame/<media_id>/<frame>')
def tator_frame(media_id, frame):
    if 'tator_token' in session.keys():
        token = session['tator_token']
    else:
        token = request.args.get('token')
    url = f'{current_app.config.get("TATOR_URL")}/rest/GetFrame/{media_id}?frames={frame}'
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


# view tator localization image (cropped)
@tator_bp.get('/localization-image/<localization_id>')
def tator_image(localization_id):
    if not session.get('tator_token'):
        if not request.values.get('token'):
            return {}, 400
        token = request.values.get('token')
    else:
        token = session["tator_token"]
    res = requests.get(
        url=f'{current_app.config.get("TATOR_URL")}/rest/LocalizationGraphic/{localization_id}',
        headers={'Authorization': f'Token {token}'}
    )
    if res.status_code == 200:
        base64_image = base64.b64encode(res.content).decode('utf-8')
        return Response(base64.b64decode(base64_image), content_type='image/png'), 200
    return '', 500


# update tator localization
@tator_bp.patch('/localization')
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
                host=current_app.config.get('TATOR_URL'),
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
@tator_bp.patch('/localization/good-image')
def update_tator_localization_image():
    localization_elemental_ids = request.values.getlist('localization_elemental_ids')
    version = request.values.get('version')
    try:
        for elemental_id in localization_elemental_ids:
            api = tator.get_api(
                host=current_app.config.get('TATOR_URL'),
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
