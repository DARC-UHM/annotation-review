"""
Populates the substrate attributes of video clips in Tator with information loaded from a CSV file. Before running
this script, ensure that the CSV file does not contain special characters (e.g. '%') or commas in the 'Substrate
Notes' field.

Usage: python populate_substrates.py <project_id> <section_id> <substrates csv file>
"""

import csv
import dotenv
import os
import requests
import sys

if len(sys.argv) != 4:
    print('Usage: python populate_substrates.py <project_id> <section_id> <substrates csv file>')
    sys.exit(1)

dotenv.load_dotenv()

PROJECT_ID = sys.argv[1]
SECTION_ID = sys.argv[2]
CSV_FILE = sys.argv[3]

with open(CSV_FILE, newline='') as file:
    next(file)
    reader = csv.DictReader(file)
    for row in reader:
        # get all media ids that match deployment name
        deployment_name = row['deployment'].replace('_2024', '')
        print(deployment_name)
        attributes = {
            'FOV': row['FoV'],
            'Relief': row['relief'].replace('Relief: ', ''),
            'Bedforms': row['bedforms'].replace('Bedforms: ', ''),
            'Substrate': row['Substrate (Hard/Soft)'],
            'Substrate Notes': row['Notes'],
            'Primary Substrate': row['primarySubstrate'].replace('Substrate: ', ''),
            'Secondary Substrate': row['secondarySubstrate'].replace('Substrate: ', ''),
        }
        print('New attributes:', attributes)
        res = requests.get(
            f'https://cloud.tator.io/rest/Medias/{PROJECT_ID}?section={SECTION_ID}&attribute_contains=%24name%3A%3A{deployment_name}',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Token {os.getenv("TATOR_TOKEN")}',
            }
        )
        media_ids = [media['id'] for media in res.json()]
        print(f'Found {len(media_ids)} media files')
        # update attributes for each media id
        for media_id in media_ids:
            print(f'Updating media id: {media_id}...', end='')
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
            print(req.json())
