"""
Adds a state of "Sub Mode": "Transect" to all the medias in the given file. If a "Sub Mode" state already exists
for a media, it is skipped instead of adding an additional state.

Usage: python add_transect_states.py <file-containing-media-ids>

Example: python add_transect_states.py media_ids.txt
"""

import os

import dotenv
import requests
import sys

TATOR_REST_URL = 'https://cloud.tator.io/rest'

if len(sys.argv) != 2:
    print('Usage: python add_transect_states.py <file-containing-media-ids>')
    exit(1)

dotenv.load_dotenv()

HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'Token {os.getenv("TATOR_TOKEN")}',
}

with open(sys.argv[1]) as f:
    MEDIA_IDS= f.read().strip().split('\n')

states_res = requests.get(
    url=f'{TATOR_REST_URL}/States/26?media_id={",".join(MEDIA_IDS)}',
    headers=HEADERS
)

if (states_res.status_code != 200):
    print('Error connecting to Tator', states_res.json())
    exit(1)

medias_with_transect_state = set()

for state in states_res.json():
    if state['type'] == 847:
        for media_id in state['media']:
            medias_with_transect_state.add(str(media_id))

for media_id in MEDIA_IDS:
    if media_id in medias_with_transect_state:
        print(f'Skipping media {media_id}, already has transect state added')
        continue
    json_data = {
        'type': 847,
        'media_ids': [
            int(media_id)
        ],
        'frame': 25,
        'attributes': {
            'Mode': 'Transect'
        },
        'version': 45,
        'name': 'Sub Mode'
    }
    states_post_res = requests.post(
        url=f'{TATOR_REST_URL}/States/26',
        headers=HEADERS,
        json=json_data
    )
    if (states_post_res.status_code != 201):
        print('Error adding state', states_res.json())
        exit(1)
    print(states_post_res.json())
