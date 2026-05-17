"""
General endpoints for Tator that are used throughout the application.

/tator/login [POST]
/tator/token [GET]
/tator/logout [GET]
/tator/projects [GET]
/tator/sections?project=<project_id> [GET]
/tator/refresh-sections [GET]
/tator/frame/<media_id>/<frame> [GET]
/tator/localization-image/<localization_id> [GET]
/tator/localization [PATCH]
/tator/localization/good-image [PATCH]
"""

import json

import tator
import requests
from flask import current_app, request, session, Response

from . import tator_bp
from ..util.constants import TERM_YELLOW, TERM_RED, TERM_NORMAL
from application.tator.tator_type import TatorLocalizationType
from application.tator.tator_rest_client import TatorRestClient


# log in to tator (get token from tator)
@tator_bp.post('/login')
def tator_login():
    try:
        token = TatorRestClient.login(
            tator_url=current_app.config.get('TATOR_URL'),
            username=request.values.get('username'),
            password=request.values.get('password'),
        )
        session['tator_token'] = token
        return {'username': request.values.get('username')}, 200
    except requests.HTTPError as e:
        return {}, e.response.status_code


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
@tator_bp.get('/sections')
def tator_sections():
    def should_skip(section_path):
        skip_substrings = ('test', 'toplevelsectionname', 'bad_imports')
        section_path_lower = (section_path or '').lower()
        return any(skip_substring in section_path_lower for skip_substring in skip_substrings)

    project_id = request.args.get('project')
    try:
        sections = {}
        section_list = tator.get_api(
            host=current_app.config.get('TATOR_URL'),
            token=session.get('tator_token'),
        ).get_section_list(project_id)
        # just doing two passes to simplify the logic
        for section in section_list:  # first pass - get top-level sections
            if should_skip(section.path):
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
            if len(path_parts) <= 2:
                continue
            if len(path_parts) == 3:  # expect these to all be dropcam deployments
                parent_name, folder_name, _ = path_parts
                if folder_name == 'sub':
                    continue  # expedition.sub.exploratory|transect are subfolder markers, not deployments
                if sections.get(parent_name) is None:
                    print(f'{TERM_YELLOW}WARNING: Skipping sub-section "{section.name}" because parent section "{parent_name}" was not found{TERM_NORMAL}')
                    continue
                if sections[parent_name]['folders'].get(folder_name) is None:
                    sections[parent_name]['folders'][folder_name] = []
                sections[parent_name]['folders'][folder_name].append({'id': section.id, 'name': section.name})
            elif len(path_parts) == 4:  # sub structure: expedition.sub.exploratory|transect.deployment
                parent_name, folder_name, sub_folder_name, _ = path_parts
                if folder_name != 'sub':
                    print(f'Skipping section with unexpected 4-level path format: "{section.path}"')
                    continue
                if sections.get(parent_name) is None:
                    print(f'{TERM_YELLOW}WARNING: Skipping sub-section "{section.name}" because parent section "{parent_name}" was not found{TERM_NORMAL}')
                    continue
                if sections[parent_name]['folders'].get('sub') is None:
                    sections[parent_name]['folders']['sub'] = {}
                if sections[parent_name]['folders']['sub'].get(sub_folder_name) is None:
                    sections[parent_name]['folders']['sub'][sub_folder_name] = []
                sections[parent_name]['folders']['sub'][sub_folder_name].append({'id': section.id, 'name': section.name})
            else:
                print(f'Skipping section with unexpected path format: "{section.path}"')
        # sort deployment lists by name
        for section_attributes in sections.values():
            if len(section_attributes['folders']) > 0:
                for folder_data in section_attributes['folders'].values():
                    if isinstance(folder_data, dict):
                        for sub_list in folder_data.values():
                            sub_list.sort(key=lambda x: x['name'])
                    else:
                        folder_data.sort(key=lambda x: x['name'])
        return list(sections.values()), 200
    except tator.openapi.tator_openapi.exceptions.ApiException as e:
        print(f'{TERM_RED}ERROR: Unable to fetch Tator sections:{TERM_NORMAL} {e}')
        return {'500': 'Error fetching Tator sections'}, 500


# get all media for one or more sections
@tator_bp.get('/media')
def section_media():
    project_id = request.values.get('project')
    section_ids = request.values.getlist('section')
    if not project_id or not section_ids:
        return {'error': 'project and section are required'}, 400
    tator_client = TatorRestClient(current_app.config.get('TATOR_URL'), session.get('tator_token'))
    try:
        media_list = []
        for section_id in section_ids:
            media_list += tator_client.get_medias_for_section(project_id=int(project_id), sections=[int(section_id)])
        media_list.sort(key=lambda x: x['name'])
        return [{'name': m['name'], 'id': m['id']} for m in media_list], 200
    except Exception as e:
        print(f'{TERM_RED}ERROR: Unable to fetch media list from Tator:{TERM_NORMAL} {e}')
        return {'500': 'Error fetching Tator media'}, 500


# view tator video frame (not cropped)
@tator_bp.get('/frame/<media_id>/<frame>')
def tator_frame(media_id, frame):
    token = session.get('tator_token') or request.args.get('token')
    if not token:
        return {}, 400
    tator_client = TatorRestClient(current_app.config.get('TATOR_URL'), token)
    quality = 650 if request.values.get('preview') else None
    image = tator_client.get_frame(int(media_id), frame=int(frame), quality=quality)
    return Response(image, content_type='image/png'), 200


# view tator localization image (cropped)
@tator_bp.get('/localization-image/<localization_id>')
def tator_image(localization_id):
    token = session.get('tator_token') or request.values.get('token')
    if not token:
        return {}, 400
    tator_client = TatorRestClient(current_app.config.get('TATOR_URL'), token)
    image = tator_client.get_localization_graphic(int(localization_id))
    return Response(image, content_type='image/png'), 200


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
    }
    if attracted := request.values.get('attracted'):
        attributes['Attracted'] = attracted
    if upon := request.values.get('upon'):
        attributes['Upon'] = upon
    if size := request.values.get('size'):
        attributes['Size'] = size
    try:
        for localization in localization_id_types:
            this_attributes = attributes.copy()
            if TatorLocalizationType.is_dot(localization['type']):
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
    except tator.openapi.tator_openapi.exceptions.ApiException as e:
        print(f'{TERM_RED}ERROR: Unable to update Tator localization:{TERM_NORMAL} {e.body}')
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
