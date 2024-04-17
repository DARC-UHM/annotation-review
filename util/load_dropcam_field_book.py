import dotenv
import os
import pandas as pd
import requests
import sys


if len(sys.argv) != 3:
    print('Usage: python load_dropcam_field_book.py <expedition name> <path to dropcam fieldbook xlsx file>')
    sys.exit()

dotenv.load_dotenv()

EXPEDITION_NAME = sys.argv[1]
FIELDBOOK_XLSX_PATH = sys.argv[2]

# open xlsx file
fieldbook_df = pd.read_excel(FIELDBOOK_XLSX_PATH)

# create json payload
deployments = []
for index, row in fieldbook_df.iterrows():
    deployment = {
        'deployment_name': row['ps_station_id'],
        'lat': row['lat_in'],
        'long': row['lon_in'],
        'depth_m': row['depth_m'] if not pd.isnull(row['depth_m']) else None,
        'bait_type': row['bait_type'],
    }
    deployments.append(deployment)

res = requests.post(
    'http://localhost:5000/dropcam-fieldbook',
    json={
        'expedition_name': EXPEDITION_NAME,
        'deployments': deployments,
    },
    headers={'API-Key': os.getenv('DARC_REVIEW_API_KEY')},
)
print(res.status_code)
