import os
import sys

import requests
import tator

TATOR_URL = 'https://cloud.tator.io'


def get_deployment_section_id_map() -> dict:
    deployment_section_id_map = {}

    print('Fetching section details from Tator...', end='')
    sys.stdout.flush()

    try:
        section_list = tator.get_api(
            host=TATOR_URL,
            token=os.getenv('TATOR_TOKEN'),
        ).get_section_list(26)  # hardcoded NGS-ExTech Project
        for section in section_list:
            if 'bad_imports' in section.path or 'TopLevelSectionName' in section.path:
                continue
            deployment_section_id_map[section.name] = section.id
    except tator.openapi.tator_openapi.exceptions.ApiException as e:
        print(f'ERROR: Unable to fetch Tator sections: {e}')
        exit(1)

    print('fetched!')

    return deployment_section_id_map


def print_progress_bar(iteration: int, total: int, prefix: str = '', suffix: str = ''):
    """
    Call in a loop to create terminal progress bar
    """
    length = 100
    term_blue = '\033[1;34m'
    term_normal = '\033[1;37;0m'
    percent = round((100 * (iteration / float(total))), 1)
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} {term_blue}|{bar}|{term_normal} {percent}% {suffix}', end='\r')
    if iteration == total:
        print()


def get_transect_media(expedition_name: str, media_names: list[str], tator_token: str) -> list[dict]:
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {tator_token}',
    }

    section_res = requests.get(
        url=f'{TATOR_URL}/rest/Sections/26',
        headers=headers,
    )

    if section_res.status_code != 200:
        print('Error connecting to Tator', section_res.json())
        exit(1)

    section_ids = []

    for section in section_res.json():
        parts = section['path'].split('.')
        if len(parts) != 3:
            continue
        if parts[0] == expedition_name and parts[1] == 'sub':
            section_ids.append(str(section['id']))

    media_res = requests.get(
        url=f'{TATOR_URL}/rest/Medias/26?multi_section={",".join(section_ids)}',
        headers=headers,
    )

    if section_res.status_code != 200:
        print('Error connecting to Tator', media_res.json())
        exit(1)

    return [
        {
            'name': media['name'],
            'id': media['id'],
            'start_time': media['attributes']['Start Time'],
            'fps': media['fps'],
        } for media in media_res.json() if media['name'] in media_names]
