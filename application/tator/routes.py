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

from tator_scripts.populate_ctd import TERM_NORMAL
from . import tator_bp
from ..util.constants import TERM_YELLOW, TERM_RED
from ..util.tator_localization_type import TatorLocalizationType


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


# get a list of sections associated with a project from tator
@tator_bp.get('/sections/<project_id>')
def tator_sections(project_id):
    def should_skip(section_path):
        section_path_lower = section_path.lower()
        return 'test' in section_path_lower or 'toplevelsectionname' in section_path_lower

    try:
        sections = {}
        section_list = tator.get_api(
            host=current_app.config.get('TATOR_URL'),
            token=session.get('tator_token'),
        ).get_section_list(project_id)
        # just doing two passes to simplify the logic
        for section in section_list:  # first pass - get top-level sections
            if should_skip(section.path):
                print(f'Skipping section with test path: "{section.path}" and name: "{section.name}"')
                continue
            path_parts = section.path.split('.')
            if len(path_parts) != 1:
                continue  # not a top-level section
            section_path_name = path_parts[0]
            if section_path_name == 'None':
                # handle case where top-level section is named "None" 🙄 (PNG DOEX010, Solomons DOEX010, etc?)
                section_path_name = section.name
            if sections.get(section_path_name):
                print(f'{TERM_YELLOW}WARNING: duplicate expedition-level section name "{section_path_name}" detected{TERM_NORMAL}')
            sections[section_path_name] = {
                'id': section.id,
                'name': section.name,
                'folders': {},
            }
        for section in section_list:  # second pass - get subsections
            if should_skip(section.path):
                continue
            path_parts = section.path.split('.')
            if len(path_parts) == 1:
                continue
            if len(path_parts) != 3:
                if path_parts[1] == 'dscm' or path_parts[1] == 'sub':
                    continue
                print(f'Skipping section with unexpected path format: "{section.path}"')
                continue
            parent_name, folder_name, _ = path_parts
            if sections.get(parent_name) is None:
                print(f'{TERM_YELLOW}WARNING: Skipping sub-section "{section.name}" because parent section "{parent_name}" was not found{TERM_NORMAL}')
                continue
            if sections[parent_name]['folders'].get(folder_name) is None:
                sections[parent_name]['folders'][folder_name] = []
            sections[parent_name]['folders'][folder_name].append({
                'id': section.id,
                'name': section.name,
            })
        return list(sections.values()), 200
    except tator.openapi.tator_openapi.exceptions.ApiException as e:
        print(f'{TERM_RED}ERROR: Unable to fetch Tator sections:{TERM_NORMAL} {e}')
        return {'500': 'Error fetching Tator sections'}, 500


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
        'Morphospecies': request.values.get('morphospecies'),
        'Identified By': request.values.get('identified_by'),
        'Notes': request.values.get('notes'),
        'Attracted': request.values.get('attracted'),
    }
    try:
        for localization in localization_id_types:
            this_attributes = attributes.copy()
            if localization['type'] == TatorLocalizationType.DOT.value:
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
