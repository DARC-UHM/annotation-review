"""
Populates the 'DO Temperature (celsius)' and the 'DO Concentration Salin Comp (mol per L)' attributes of localizations
in Tator with values pulled from a CSV file located in the Dropbox. Start timestamps must be synced in Tator before
running this script.

Since the camera video data and the sensor data do not appear to be synced, this script will ASSUME that the video data
has the correct date and time and will use the deployment's 'Arrival' time as the correct bottom time. The script finds
the bottom time in the CTD CSV file by finding where the depth is greater than or equal to the depth in the fieldbook,
and compares the time at that row with the camera bottom time to find a time offset. This offset is used to find the
CTD data that corresponds to each localization.

To run this script, you must have a .env file in the root of the repository the following variables:
    - DROPBOX_ACCESS_TOKEN: Access token for the Dropbox API (https://www.dropbox.com/developers/apps)
    - DROPBOX_FOLDER_PATH: Path to the folder in Dropbox containing the deployment's video files
    - TATOR_TOKEN: Tator API token
    - DARC_REVIEW_API_KEY: DARC Review API key

Usage: python populate_ctd.py <project_id> <section_id> <deployment_name>
"""

import dotenv
import dropbox
import os
import pandas as pd
import requests
import sys
import time

from datetime import datetime, timedelta


TERM_RED = '\033[1;31;48m'
TERM_YELLOW = '\033[1;93m'
TERM_NORMAL = '\033[1;37;0m'

if len(sys.argv) != 4:
    print('Usage: python load_video_start_times.py <project_id> <section_id> <deployment_name>')
    sys.exit()

dotenv.load_dotenv()

TATOR_TOKEN = os.getenv('TATOR_TOKEN')
PROJECT_ID = sys.argv[1]
SECTION_ID = sys.argv[2]
DEPLOYMENT_NAME = sys.argv[3]

# get list of media ids in deployment
print(f'Fetching media IDs for deployment {DEPLOYMENT_NAME}...', end='')
sys.stdout.flush()
media_ids = {}
bottom_time = None
arrival_time = None
camera_bottom_unix_timestamp = None
res = requests.get(
    url=f'https://cloud.tator.io/rest/Medias/{PROJECT_ID}?section={SECTION_ID}&attribute_contains=%24name%3A%3A{DEPLOYMENT_NAME}',
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Token {TATOR_TOKEN}',
    })
if res.status_code != 200:
    print(f'\n{TERM_RED}Error fetching localizations: {res.json()}{TERM_NORMAL}')
    exit(1)
for media in res.json():
    if not media['attributes'].get('Start Time'):
        print(f'Media {media["id"]} does not have a start timestamp')
        exit(1)
    media_ids[media['id']] = media['attributes']['Start Time']
    if media['attributes'].get('Arrival') and media['attributes']['Arrival'] != '':
        video_start_timestamp = datetime.fromisoformat(media["attributes"]["Start Time"])
        bottom_time = video_start_timestamp + timedelta(seconds=int(int(media['attributes']['Arrival'].split('|')[0]) / 30))
        camera_bottom_unix_timestamp = time.mktime(bottom_time.timetuple())
print(f'fetched {len(media_ids)} media IDs')

if bottom_time is None:
    print(f'{TERM_RED}No media with arrival time found{TERM_NORMAL}')
    exit(1)

# get all localizations in deployment
print(f'Fetching localizations...', end='')
sys.stdout.flush()
localizations = []
get_localization_res = requests.get(
    url=f'https://cloud.tator.io/rest/Localizations/{PROJECT_ID}?media_id={",".join(map(str, media_ids))}',
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Token {TATOR_TOKEN}',
    }
)
localizations += get_localization_res.json()
print(f'fetched {len(localizations)} localizations')

# find the first row in the CSV where the depth is greater than or equal to the depth in the fieldbook
req = requests.get(
    url=f'https://hurlstor.soest.hawaii.edu:5000/dropcam-fieldbook/{SECTION_ID}',
    headers={
        'API-Key': os.getenv('DARC_REVIEW_API_KEY'),
    },
)
if req.status_code != 200:
    print(f'{TERM_RED}Error fetching fieldbook: staus code {req.status_code}{TERM_NORMAL}')
    exit(1)
fieldbook = req.json()['deployments']
deployment_depth_m = next((d['depth_m'] for d in fieldbook if d['deployment_name'] == DEPLOYMENT_NAME), None)
if deployment_depth_m is None:
    print(f'{TERM_RED}Deployment {DEPLOYMENT_NAME} not found in fieldbook{TERM_NORMAL}')
    exit(1)

# get the csv for the deployment
print(f'Fetching CTD CSV file...', end='')
dbx = dropbox.Dropbox(os.getenv('DROPBOX_ACCESS_TOKEN'))  # create a Dropbox client instance
df = None
folder_path = f'{os.getenv("DROPBOX_FOLDER_PATH")}/{DEPLOYMENT_NAME}/Sensor'
try:
    # get the folder metadata
    folder_metadata = dbx.files_list_folder(folder_path)
    for entry in folder_metadata.entries:  # iterate over the entries in the folder
        path = os.path.join(folder_path, entry.name)
        if isinstance(entry, dropbox.files.FileMetadata) and entry.name[-3:].lower() == 'csv':
            _, res = dbx.files_download(path)
            print('fetched!')
            print(path)
            df = pd.read_csv(res.raw)
except dropbox.exceptions.ApiError as e:
    print(f'{TERM_RED}Error connecting to Dropbox: {e}{TERM_NORMAL}')
    exit(1)

if df is None:
    print(f'{TERM_RED}No CTD CSV file found in Dropbox{TERM_NORMAL}')
    exit(1)

print(f'\nDeployment depth: {deployment_depth_m} m')
print(f'Video bottom arrival time unix: {camera_bottom_unix_timestamp} ({bottom_time})')

# find the row in the CSV that matches the bottom time
bottom_row = df.loc[df['Depth (meters)'] >= deployment_depth_m].iloc[0]
print(f'Sensor bottom data arrival time unix: {bottom_row["Dropcam Timestamp (s)"]}')

offset = camera_bottom_unix_timestamp - bottom_row['Dropcam Timestamp (s)']
# parse time difference to hours, minutes, seconds
delta_offset = timedelta(seconds=offset)
print(f'Offset: {offset} seconds ({delta_offset})')

print('\nSyncing CTD data...')
# for each localization, populate the DO Temperature and DO Concentration Salin Comp attributes
for localization in localizations:
    # get the timestamp of the localization
    video_start_timestamp = datetime.fromisoformat(media_ids[localization['media']])
    this_timestamp = video_start_timestamp + timedelta(seconds=localization['frame'] / 30)
    unix_timestamp = time.mktime(this_timestamp.timetuple())
    # find the row in the CSV that matches the timestamp
    converted_timestamp = unix_timestamp - offset
    row = df.loc[df['Dropcam Timestamp (s)'] == converted_timestamp]
    try:
        do_temp = row['DO Temperature (celsius)'].values[0]
        do_concentration = row['DO Concentration Salin Comp (mol/L)'].values[0]
        depth = row['Depth (meters)'].values[0]
    except IndexError:
        print(f'{TERM_RED}No CTD data found for localization {localization["id"]}{TERM_NORMAL}')
        print(localization)
        exit(1)

    if do_temp < 0 or do_temp > 35:
        print(f'{TERM_YELLOW}WARNING: DO Temperature out of range (0-35): {do_temp}{TERM_NORMAL}')
    if do_concentration < 0 or do_concentration > 320:
        print(f'{TERM_YELLOW}WARNING: DO Concentration out of range (0-320): {do_concentration}{TERM_NORMAL}')
    if depth + 10 < deployment_depth_m:
        print(f'{TERM_YELLOW}WARNING: Unexpected depth: {depth} (deployment depth was {deployment_depth_m}){TERM_NORMAL}')

    # update the localization
    update_res = requests.patch(
        url=f'https://cloud.tator.io/rest/Localization/{localization["id"]}',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Token {TATOR_TOKEN}',
        },
        json={
            'attributes': {
                'DO Temperature (celsius)': do_temp,
                'DO Concentration Salin Comp (mol per L)': do_concentration,
            }
        },
    )
    print(update_res.json())

# pau
os.system('say "CTD synced."')
