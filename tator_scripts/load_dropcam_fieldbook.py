"""
Populates the fieldbook information on the DARC external review server for a given expedition. Populates lat/long,
depth, and bait type information for both internal and external review pages.

Usage:    python load_dropcam_fieldbook.py <expedition_name> <path to dropcam fieldbook xlsx>
Example:  python load_dropcam_fieldbook.py DOEX0112_Tuvalu /Users/darc/Downloads/TUV_2025_dscm_fieldbook.xlsx
"""

import dotenv
import os
import pandas as pd
import requests
import sys
import tator


if len(sys.argv) != 3:
    print('Usage: python load_dropcam_fieldbook.py <expedition_name> <path to dropcam fieldbook xlsx>')
    sys.exit()

dotenv.load_dotenv()

EXPEDITION_NAME = sys.argv[1]
FIELDBOOK_XLSX_PATH = sys.argv[2]

deployment_section_id_map = {}

print('Fetching section details from Tator...', end='')
sys.stdout.flush()

try:
    section_list = tator.get_api(
        host='https://cloud.tator.io',
        token=os.getenv('TATOR_TOKEN'),
    ).get_section_list(26)  # hardcoded NGS-ExTech Project
    for section in section_list:  # second pass - get subsections
        deployment_section_id_map[section.name] = section.id
except tator.openapi.tator_openapi.exceptions.ApiException as e:
    print(f'ERROR: Unable to fetch Tator sections: {e}')
    exit(1)

print('fetched!')

# open xlsx file
fieldbook_xlsx = pd.ExcelFile(FIELDBOOK_XLSX_PATH)
fieldbook_df = pd.read_excel(fieldbook_xlsx, 'deployments')

# create json payload
deployments = []
for index, row in fieldbook_df.iterrows():
    deployment = {
        'deployment_name': row['ps_site_id'],
        'lat': row['lat_in'],
        'long': row['lon_in'],
        'depth_m': row['depth_m'] if not pd.isnull(row['depth_m']) else None,
        'bait_type': row['bait_type'],
    }
    deployments.append(deployment)

for deployment in deployments:
    deployment_name = deployment['deployment_name']
    section_id = deployment_section_id_map.get(deployment_name)
    if section_id is None:
        print(f'WARNING: Unable to find section ID for deployment {deployment_name} in Tator. Will skip this deployment.')
        continue
    deployment['section_id'] = section_id
    res = requests.post(
        'https://hurlstor.soest.hawaii.edu:5000/dropcam-fieldbook',
        json={
            'section_id': section_id,
            'expedition_name': EXPEDITION_NAME,
            'deployments': [deployment],
        },
        headers={'API-Key': os.getenv('DARC_REVIEW_API_KEY')},
    )
    if res.status_code not in [200, 201]:
        print(f'ERROR: Unable to upload fieldbook for {deployment_name} 😔')
    print(res.status_code, res.json())

print('Done!')
