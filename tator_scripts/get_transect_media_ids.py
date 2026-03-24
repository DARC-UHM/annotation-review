"""
Prints all the transect media IDs given an expedition name and a file containing a list of media names separated
by a newline.

Usage: python get_transect_media_ids.py <expedition-name> <file-containing-media-names>

Example: python get_transect_media_ids.py TUV_2025 media_names.txt
"""

import os

import dotenv
import requests
import sys


TATOR_REST_URL = 'https://cloud.tator.io/rest'

if len(sys.argv) != 3:
    print('Usage: python get_transect_media_ids.py <expedition-name> <file-containing-media-names>')
    exit(1)

dotenv.load_dotenv()

EXPEDITION_NAME = sys.argv[1]
FILE_NAME = sys.argv[2]
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'Token {os.getenv("TATOR_TOKEN")}',
}

with open(FILE_NAME) as f:
    MEDIA_NAMES = f.read().strip().split('\n')

section_res = requests.get(f'{TATOR_REST_URL}/Sections/26', headers=HEADERS)

if section_res.status_code != 200:
    print('Error connecting to Tator', section_res.json())
    exit(1)

section_ids = []

for section in section_res.json():
    parts = section['path'].split('.')
    if len(parts) != 3:
        continue
    if parts[0] == EXPEDITION_NAME and parts[1] == 'sub':
        section_ids.append(str(section['id']))

media_res = requests.get(f'{TATOR_REST_URL}/Medias/26?multi_section={",".join(section_ids)}', headers=HEADERS)

if section_res.status_code != 200:
    print('Error connecting to Tator', media_res.json())
    exit(1)

for media in media_res.json():
    if media['name'] in MEDIA_NAMES:
        print(media['id'])
