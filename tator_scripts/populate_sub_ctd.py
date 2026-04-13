"""
Populates CTD (position, temperature, depth) attributes on Tator localizations for
sub/transect deployments, using sensor data (Qinsy CSV files) stored in Dropbox.

For each transect in the expedition metadata, the script:
  1. Fetches the Qinsy sensor CSV from Dropbox
  2. Fetches all localizations for the transect from Tator
  3. Matches each localization to the nearest Qinsy row by timestamp
  4. Patches the localization's Position, DO Temperature, and Depth attributes in Tator

To run this script, you must have a .env file in the root of the repository with the following variables:
    - DROPBOX_ACCESS_TOKEN: Access token for the Dropbox API (https://www.dropbox.com/developers/apps)
    - TATOR_TOKEN: Tator API token

Usage: python populate_sub_ctd.py <expedition_name> [--days-offset <int>] [--dry-run]

Arguments:
    expedition_name     Name of the expedition (e.g. TUV_2025)
    --days-offset       Number of days to offset localization timestamps to align with Qinsy data (default: 0)
    --dry-run           Print changes without writing to Tator

Examples:
    python populate_sub_ctd.py TUV_2025
    python populate_sub_ctd.py TUV_2025 --days-offset 1 --dry-run
"""

import argparse
import datetime
import dotenv
import dropbox
import io
import os
import pandas as pd
import requests
import random
import sys

from tator_script_helper_functions import get_transect_media

TERM_RED = '\033[1;31;48m'
TERM_YELLOW = '\033[1;93m'
TERM_GREEN = '\033[1;32m'
TERM_NORMAL = '\033[1;37;0m'
PROJECT_ID = 26
TATOR_URL = 'https://cloud.tator.io'


def populate_ctd(expedition_name: str, days_offset: int, dry_run: bool):
    if dry_run:
        print('\n\n========= DRY RUN =========\n\n')

    expedition_sub_folder_path = f'/Pristine Seas Dropcam Data/sub/{expedition_name}'
    dropbox_client = dropbox.Dropbox(os.getenv('DROPBOX_ACCESS_TOKEN'))

    # get the names all the transect media in the expedition, along with the time_start_qinsy
    print('Fetching transect media information from Dropbox...', end='')
    sys.stdout.flush()

    metadata_df = get_metadata_df(dropbox_client, expedition_sub_folder_path)

    if metadata_df is None:
        print(f'\n{TERM_RED}No expedition metadata file found in Dropbox{TERM_NORMAL}')
        exit(1)

    transect_rows_df = metadata_df[metadata_df['transect'] == True][['filename', 'ps_site_id', 'local_date', 'time_start_qinsy']]
    transect_rows_df['qinsy_timestamp'] = pd.to_datetime(transect_rows_df['local_date'].astype(str) + ' ' + transect_rows_df['time_start_qinsy'].astype(str))
    print(f'Found {len(transect_rows_df)} deployments containing transects.')

    deployment_names = transect_rows_df['ps_site_id'].unique()
    file_names = transect_rows_df['filename'].unique()
    media_list = get_transect_media(expedition_name, file_names, TATOR_TOKEN)

    # for each deployment that has a transect
    for deployment in deployment_names:
        print(f'\nProcessing deployment {deployment}...')

        # get matching file names for this deployment
        deployment_file_names = transect_rows_df[transect_rows_df['ps_site_id'] == deployment]['filename'].unique()
        deployment_media = [media for media in media_list if media['name'] in deployment_file_names]
        print(f'Found {len(deployment_file_names)} transects for this deployment.')

        # grab qinsy file for deployment
        deployment_qinsy_folder_path = f'{expedition_sub_folder_path}/{deployment.replace("_", "-")}/Qinsy'
        qinsy_df = get_qinsy_df(dropbox_client, deployment_qinsy_folder_path)
        if qinsy_df is None:
            print(f'\n{TERM_RED}No Qinsy file found for deployment {deployment} in Dropbox{TERM_NORMAL}')
            exit(1)

        for index, media in enumerate(deployment_media):
            print(f'\nProcessing {media["name"]} (transect {index + 1}/{len(deployment_media)} for this deployment)...')
            media_row = transect_rows_df[transect_rows_df['filename'] == media['name']]
            start_time = media_row.iloc[0]['qinsy_timestamp']

            # get all localizations from tator for this transect
            localizations = get_localizations(media['id'])

            for localization in localizations:
                localization_timestamp = start_time + datetime.timedelta(
                    days=days_offset,
                    seconds=localization['frame'] / media['fps'],
                )
                localization_timestamp = pd.Timestamp(localization_timestamp).round('s').to_pydatetime()
                localization_timestamp = localization_timestamp.replace(tzinfo=None)
                if localization_timestamp not in qinsy_df.index:
                    print(f'{TERM_RED}No Qinsy data for timestamp {localization_timestamp} (localization {localization["id"]}), exiting{TERM_NORMAL}')
                    exit(1)
                matched_row = qinsy_df.loc[localization_timestamp]
                lat = parse_coord(matched_row['Steered Node Latitude'])
                long = parse_coord(matched_row['Steered Node Longitude'])
                temp_c = matched_row['TMP Value']
                depth_m = matched_row['Depth']

                patch_localization_ctd(
                    localization=localization,
                    lat=lat,
                    long=long,
                    temp_c=temp_c,
                    depth_m=depth_m,
                    dry_run=dry_run,
                )


def get_metadata_df(dropbox_client: dropbox.Dropbox, expedition_sub_folder_path: str):
    try:
        folder_metadata = dropbox_client.files_list_folder(expedition_sub_folder_path)
        for entry in folder_metadata.entries:
            if isinstance(entry, dropbox.files.FileMetadata) and entry.name.endswith('.xlsx') and 'metadata' in entry.name.lower():
                path = os.path.join(expedition_sub_folder_path, entry.name)
                _, res = dropbox_client.files_download(path)
                print('fetched!')
                print(f'Dropbox file location: {path}')
                return pd.read_excel(io.BytesIO(res.content), engine='openpyxl')
    except dropbox.exceptions.ApiError as e:
        print(f'\n{TERM_RED}Error connecting to Dropbox: {e}{TERM_NORMAL}')
        print(f'Tried looking for expedition metadata file in folder: {expedition_sub_folder_path}')
        print('Is this the correct folder path?')
        exit(1)
    except dropbox.exceptions.AuthError as e:
        print(f'\n\n{TERM_RED}Error connecting to Dropbox: {e}{TERM_NORMAL}')
        exit(1)


def get_qinsy_df(dropbox_client: dropbox.Dropbox, qinsy_folder_path: str):
    df = None
    try:
        folder_metadata = dropbox_client.files_list_folder(qinsy_folder_path)
        for entry in folder_metadata.entries:
            if isinstance(entry, dropbox.files.FileMetadata) and not entry.name.startswith('.'):
                path = os.path.join(qinsy_folder_path, entry.name)
                _, res = dropbox_client.files_download(path)
                print(f'Qinsy file location: {path}')
                df = pd.read_csv(res.raw)
    except dropbox.exceptions.ApiError as e:
        print(f'\n{TERM_RED}Error connecting to Dropbox: {e}{TERM_NORMAL}')
        print(f'Tried looking for expedition metadata file in folder: {qinsy_folder_path}')
        print('Is this the correct folder path?')
        exit(1)
    except dropbox.exceptions.AuthError as e:
        print(f'\n\n{TERM_RED}Error connecting to Dropbox: {e}{TERM_NORMAL}')
        exit(1)
    for expected_col_header in [
        'Steered Node Latitude',
        'Steered Node Longitude',
        'TMP Value',
    ]:
        if expected_col_header not in df.keys():
            print(f'\n{TERM_RED}Sensor CSV not in expected format: Missing column with header "{expected_col_header}"{TERM_NORMAL}')
            print(f'See CSV file here: https://www.dropbox.com/home{qinsy_folder_path}')
            exit(1)
    # just using pressure for depth, it's close enough
    df = df.rename(columns={'PRS Value': 'Depth'})
    df['Timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%m/%d/%Y %H:%M:%S')
    df = df.set_index('Timestamp')
    return df[['Steered Node Latitude', 'Steered Node Longitude', 'TMP Value', 'Depth']]


def get_localizations(media_id: int) -> list[dict]:
    url = f'{TATOR_URL}/rest/Localizations/{PROJECT_ID}?media_id={media_id}'
    res = requests.get(url=url, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Token {TATOR_TOKEN}',
    })
    res.raise_for_status()
    return res.json()


def parse_coord(coord_str: str) -> float:
    """
    Parse a coordinate string in 'degrees;decimal_minutes + hemisphere' format.
    Example: '5;37.9663846S' → -5.6328, '176;03.6874366E' → 176.0614
    """
    hemisphere = coord_str[-1]
    degrees, minutes = coord_str[:-1].split(';')
    decimal = float(degrees) + float(minutes) / 60
    if hemisphere in ('S', 'W'):
        decimal = -decimal
    return decimal


def patch_localization_ctd(localization: dict, lat: float, long: float, temp_c: float, depth_m: float, dry_run: bool):
    if dry_run:
        print(f'\n{TERM_YELLOW}DRY RUN: Would update localization {localization["id"]} at frame {localization["frame"]}'
              f' with Position=({lat}, {long}), DO Temperature={temp_c}C, Depth={depth_m}m{TERM_NORMAL}')
        return
    res = requests.patch(
        url=f'{TATOR_URL}/rest/Localization/{localization["id"]}',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Token {TATOR_TOKEN}',
        },
        json={
            'attributes': {
                'Position': [long, lat],
                'DO Temperature (celsius)': temp_c,
                'Depth': depth_m,
            },
        }
    )
    if res.status_code != 200:
        print(f'\n{TERM_RED}Error updating localization {localization["id"]} in Tator: {res.json()}{TERM_NORMAL}')
        exit(1)
    print(res.json()['message'])


if __name__ == '__main__':
    dotenv.load_dotenv()
    TATOR_TOKEN = os.getenv('TATOR_TOKEN')

    parser = argparse.ArgumentParser(description='Syncs CTD data from Dropbox to Tator')
    parser.add_argument('expedition_name', type=str, help='Name of the expedition (e.g. DOEX0112_Tuvalu)')
    parser.add_argument('--days-offset', type=int, default=0, help='Number of days to offset the localization timestamps (default: 0)')
    parser.add_argument('--dry-run', action='store_true', help='Do not update Tator, just print the changes (for development)')
    args = parser.parse_args()

    populate_ctd(expedition_name=args.expedition_name, days_offset=args.days_offset, dry_run=args.dry_run)

    # pau
    marine_emojis = ['🦈', '🐠', '🐬', '🐋', '🐙', '🦑', '🦐', '🦞', '🦀', '🐚', '🌊']
    print()
    print(f'{args.expedition_name} complete {random.choice(marine_emojis)}')
    print()
    os.system('say "Expedition C T D synced."')
