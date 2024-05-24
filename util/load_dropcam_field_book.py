"""
Populates the fieldbook information on the DARC external review server for a given expedition. Populates lat/long,
depth, and bait type information for both internal and external review pages.

Usage:    python load_dropcam_field_book.py <section_id> <expedition_name> <path to dropcam fieldbook xlsx>
Example:  python load_dropcam_field_book.py 11922 DOEX0087_Niue /Users/darc/Downloads/NIU_dscm_fieldbook.xlsx
"""

import dotenv
import os
import pandas as pd
import requests
import sys


if len(sys.argv) != 4:
    print('Usage: python load_dropcam_field_book.py <section_id> <expedition_name> <path to dropcam fieldbook xlsx>')
    sys.exit()

dotenv.load_dotenv()

SECTION_ID = int(sys.argv[1])
EXPEDITION_NAME = sys.argv[2]
FIELDBOOK_XLSX_PATH = sys.argv[3]

# open xlsx file
fieldbook_df = pd.read_excel(FIELDBOOK_XLSX_PATH)

# create json payload
deployments = []
for index, row in fieldbook_df.iterrows():
    deployment = {
        'deployment_name': row['ps_station_id'].replace('2024_', ''),
        'lat': row['lat_in'],
        'long': row['lon_in'],
        'depth_m': row['depth_m'] if not pd.isnull(row['depth_m']) else None,
        'bait_type': row['bait_type'],
    }
    deployments.append(deployment)

res = requests.post(
    'https://hurlstor.soest.hawaii.edu:5000/dropcam-fieldbook',
    json={
        'section_id': SECTION_ID,
        'expedition_name': EXPEDITION_NAME,
        'deployments': deployments,
    },
    headers={'API-Key': os.getenv('DARC_REVIEW_API_KEY')},
)

print(res.status_code)
print(res.json())
