"""
Updates all the "upons" in a given media that are substrates in the UPONS_TO_RENAME to be lowercase. Also updates
"In water column" upons to be lowercase.

To run this script, you must have a .env file in the root of the repository with the following variable:
    - TATOR_TOKEN: Tator API token

Usage: python update_upons_lowercase_substrates.py <media_id>
"""

import os

import dotenv
import requests
import sys

UPONS_TO_RENAME = {'Sand', 'Cobble', 'Boulder', 'Rock'}  # add any other upons to rename
TATOR_REST_URL = 'https://cloud.tator.io/rest'

updated_upons = {}
skipped_upons = {}

if len(sys.argv) != 2:
    print('Usage: python update_upons_lowercase_substrates.py <media_id>')
    exit(1)

dotenv.load_dotenv()
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Token {os.getenv("TATOR_TOKEN")}',
}

media_id = sys.argv[1]

res = requests.get(
    url=f'{TATOR_REST_URL}/Localizations/26?media_id={media_id}',
    headers=headers
)

if res.status_code != 200:
    print('ERROR: Unable to get localizations from Tator')
    print(res.json())
    exit(1)
localizations = res.json()

for localization in localizations:
    upon = localization['attributes']['Upon']
    if upon in UPONS_TO_RENAME or ('water' in upon and 'column' in upon and upon[0].isupper()):
        print(f'Updating upon "{upon}"...')
        update_res = requests.patch(
            url=f'{TATOR_REST_URL}/Localization/{localization["id"]}',
            headers=headers,
            json={
                'attributes': {
                    'Upon': upon.lower()
                }
            }
        )
        update_json = update_res.json()
        print(update_json['message'])
        if update_res.status_code != 200:
            print(f'ERROR: Unable to update localization {localization["id"]}')
            exit(1)
        if upon not in updated_upons:
            updated_upons[upon] = 0
        updated_upons[upon] += 1
        print(f'New upon: "{update_json["object"]["attributes"]["Upon"]}"')
        print()
    else:
        if upon not in skipped_upons:
            skipped_upons[upon] = 0
        skipped_upons[upon] += 1
        print(f'Skipping upon: "{upon}"')
        print()

print('=================================')
print()
print('Updated upons:')
if not updated_upons:
    print('None')
for key, value in updated_upons.items():
    print(f'"{key}": {value}')
print()

print('Skipped upons:')
if not skipped_upons:
    print('None')
for key, value in skipped_upons.items():
    print(f'"{key}": {value}')
