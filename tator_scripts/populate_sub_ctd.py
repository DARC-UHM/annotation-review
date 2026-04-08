"""
Populates the 'DO Temperature (celsius)' and the 'DO Concentration Salin Comp (mol per L)' attributes of localizations
in Tator with values pulled from a CSV file located in the Dropbox. Start timestamps must be synced in Tator before
running this script.

To run this script, you must have a .env file in the root of the repository with the following variables:
    - DROPBOX_ACCESS_TOKEN: Access token for the Dropbox API (https://www.dropbox.com/developers/apps)
    - TATOR_TOKEN: Tator API token

Usage: python populate_sub_ctd.py <expedition_name> [--dry-run]

Examples:
    python populate_sub_ctd.py TUV_2025
    python populate_sub_ctd.py TUV_2025 --dry-run
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


def populate_ctd(expedition_name: str, dry_run: bool):
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

    transect_rows = metadata_df[metadata_df['transect'] == True][['filename', 'ps_site_id', 'time_start_qinsy']]
    print(f'Found {len(transect_rows)} transect deployments.')

    deployment_names = transect_rows['ps_site_id'].unique()
    file_names = transect_rows['filename'].unique()
    media_list = get_transect_media(expedition_name, file_names, TATOR_TOKEN)

    # for each folder in the sub
    for deployment in deployment_names:
        print(f'\nProcessing deployment {deployment}...')

        # get matching file names for this deployment
        deployment_file_names = transect_rows[transect_rows['ps_site_id'] == deployment]['filename'].unique()
        deployment_media_ids = [media['id'] for media in media_list if media['name'] in deployment_file_names]
        print(f'Found {len(deployment_file_names)} transects for this deployment.')

        # grab all localizations from tator for the deployment
        localizations = get_localizations(deployment_media_ids)
        print(f'Found {len(localizations)} localizations across these transects.')

        # grab qinsy file for deployment
        deployment_qinsy_folder_path = f'{expedition_sub_folder_path}/{deployment.replace("_", "-")}/Qinsy'
        qinsy_df = get_qinsy_df(dropbox_client, deployment_qinsy_folder_path)
        if qinsy_df is None:
            print(f'\n{TERM_RED}No Qinsy file found for deployment {deployment} in Dropbox{TERM_NORMAL}')
            exit(1)

        print(qinsy_df)
        for localization in localizations:
            localization_media = next((media for media in media_list if media['id'] == localization['media']), None)
            if localization_media is None:
                print(f'\n{TERM_RED}Could not find media with ID {localization['media']} in media list{TERM_NORMAL}')
                exit(1)
            media_start_time = datetime.datetime.fromisoformat(localization_media['start_time'])
            localization_timestamp = media_start_time + datetime.timedelta(seconds=localization['frame'] / localization_media['fps'])
            print(localization_timestamp)
            exit(1)
            # todo find the closest qinsy timestamp to the localization timestamp, populate CTD

    # pau
    marine_emojis = ['🦈', '🐠', '🐬', '🐋', '🐙', '🦑', '🦐', '🦞', '🦀', '🐚', '🌊']
    print()
    print(f'{expedition_name} complete {random.choice(marine_emojis)}')
    print()


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
    return df[['Date', 'Time', 'Steered Node Latitude', 'Steered Node Longitude', 'TMP Value']]


def get_localizations(media_ids: list[int]) -> list[dict]:
    url = f'{TATOR_URL}/rest/Localizations/{PROJECT_ID}?media_id={",".join(str(m) for m in media_ids)}'
    res = requests.get(url=url, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Token {TATOR_TOKEN}',
    })
    res.raise_for_status()
    return res.json()


if __name__ == '__main__':
    dotenv.load_dotenv()
    TATOR_TOKEN = os.getenv('TATOR_TOKEN')

    print('not ready yet :)')
    exit(0)

    parser = argparse.ArgumentParser(description='Syncs CTD data from Dropbox to Tator')
    parser.add_argument('expedition_name', type=str, help='Name of the expedition (e.g. DOEX0112_Tuvalu)')
    parser.add_argument('--dry-run', action='store_true', help='Do not update Tator, just print the changes (for development)')
    args = parser.parse_args()

    populate_ctd(
        expedition_name=args.expedition_name,
        dry_run=args.dry_run,
    )

    # os.system('say "Expedition C T D synced."')
