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

from tator_script_helper_functions import get_deployment_section_id_map

TERM_RED = '\033[1;31;48m'
TERM_GREEN = '\033[1;32m'
TERM_NORMAL = '\033[1;37;0m'

SUCCESS = f'{TERM_GREEN}SUCCESS{TERM_NORMAL}'
FAILED = f'{TERM_RED}FAILED{TERM_NORMAL}'

if len(sys.argv) != 3:
    print('Usage: python load_dropcam_fieldbook.py <expedition_name> <path to dropcam fieldbook xlsx>')
    sys.exit()

dotenv.load_dotenv()

EXPEDITION_NAME = sys.argv[1]
FIELDBOOK_XLSX_PATH = sys.argv[2]

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

deployment_section_id_map = get_deployment_section_id_map()

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
        print(f'{TERM_RED}ERROR: Unable to upload fieldbook for {deployment_name}{TERM_NORMAL}')
    print(f'{deployment_name} {SUCCESS if res.status_code in [200, 201] else FAILED}')
    print(res.text)

print('Done!')
