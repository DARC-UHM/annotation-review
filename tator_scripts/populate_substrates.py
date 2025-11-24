"""
Populates the substrate attributes of video clips in Tator with information loaded from a CSV file. Before running
this script, ensure that the CSV file does not contain special characters (e.g. '%') or commas in the 'Substrate
Notes' field.

To run this script, you must have a .env file in the root of the repository with the following variable:
    - TATOR_TOKEN: Tator API token

Usage: python populate_substrates.py <substrates csv file>
"""

import csv
import dotenv
import os
import requests
import sys

from tator_script_helper_functions import get_deployment_section_id_map, print_progress_bar

if len(sys.argv) != 2:
    print('Usage: python populate_substrates.py <substrates csv file>')
    sys.exit(1)

dotenv.load_dotenv()

CSV_FILE = sys.argv[1]

deployment_section_id_map = get_deployment_section_id_map()

with open(CSV_FILE, newline='') as file:
    next(file)
    reader = csv.DictReader(file)
    for row in reader:
        # get all media ids that match deployment name
        deployment_name = row['deployment']
        print()
        print('=' * 120)
        print(f'Populating media attributes for deployment {deployment_name}\n')
        section_id = deployment_section_id_map.get(deployment_name)
        if section_id is None:
            print(f'WARNING: Unable to find section ID for deployment {deployment_name} in Tator. Will skip this deployment.')
            continue
        attributes = {
            'FOV': row['FoV'],
            'Relief': row['relief'].replace('Relief: ', ''),
            'Bedforms': row['bedforms'].replace('Bedforms: ', ''),
            'Substrate': row['Substrate (Hard/Soft)'],
            'Substrate Notes': row['Notes'],
            'Primary Substrate': row['primarySubstrate'].replace('Substrate: ', ''),
            'Secondary Substrate': row['secondarySubstrate'].replace('Substrate: ', ''),
        }
        print(f'Attributes: {attributes}')
        res = requests.get(
            f'https://cloud.tator.io/rest/Medias/26?section={section_id}',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Token {os.getenv("TATOR_TOKEN")}',
            }
        )
        if res.status_code != 200:
            print(f'Error getting media ids: {res.json()["message"]}')
            exit(1)
        media_ids = [media['id'] for media in res.json()]
        if len(media_ids) == 0:
            print(f'\nNo clips found in Tator matching deployment name: {deployment_name}.')
            continue
        print(f'\nFound {len(media_ids)} media files. Updating each media file\'s attributes...')
        # update attributes for each media id
        print_progress_bar(0, len(media_ids), prefix = f'  0 / {len(media_ids)}', suffix = 'Complete')
        for index, media_id in enumerate(media_ids):
            sys.stdout.flush()
            req = requests.patch(
                f'https://cloud.tator.io/rest/Media/{media_id}',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Token {os.getenv("TATOR_TOKEN")}',
                },
                json={
                    'attributes': attributes,
                }
            )
            if req.status_code != 200:
                print(f'Error updating media id {media_id}: {req.text}')
                exit(1)
            print_progress_bar(index + 1, len(media_ids), prefix = f'  {index} / {len(media_ids)}', suffix = 'Complete')

        print()
        print(f'{deployment_name} complete!')

print("Done!")