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
            req = requests.patch(
                f'https://cloud.tator.io/rest/Media/{media_id}',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Token {os.getenv("TATOR_TOKEN")}',
                },
                json={
                    'attributes': {
                        'FOV': row['FoV'],
                        'Relief': row['relief'],
                        'Bedforms': row['bedforms'],
                        'Substrate': row['Substrate (Hard/Soft)'],
                        'Substrate Notes': row['Notes'],
                        'Primary Substrate': row['primarySubstrate'],
                        'Secondary Substrate': row['secondarySubstrate'],
                    },
                }
            )
            print(req.json())
