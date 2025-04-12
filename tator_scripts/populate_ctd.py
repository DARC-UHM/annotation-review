"""
Populates the 'DO Temperature (celsius)' and the 'DO Concentration Salin Comp (mol per L)' attributes of localizations
in Tator with values pulled from a CSV file located in the Dropbox. Start timestamps must be synced in Tator before
running this script.

Since the camera video data and the sensor data do not appear to be synced, this script will ASSUME that the video data
has the correct date and time and will use the deployment's 'Arrival' time as the correct bottom time. The script finds
the bottom time in the CTD CSV file by finding where the depth is greater than or equal to the depth in the fieldbook,
and compares the time at that row with the camera bottom time to find a time offset. This offset is used to find the
CTD data that corresponds to each localization.

To run this script, you must have a .env file in the root of the repository with the following variables:
    - DROPBOX_ACCESS_TOKEN: Access token for the Dropbox API (https://www.dropbox.com/developers/apps)
    - DROPBOX_FOLDER_PATH: Path to the folder in Dropbox containing the deployment's video files
    - TATOR_TOKEN: Tator API token

Usage: python populate_ctd.py <project_id> <section_id> <deployment_name> [--use-underscore-folder-names]
"""

import argparse
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
TERM_GREEN = '\033[1;32m'
TERM_NORMAL = '\033[1;37;0m'


def populate_ctd(project_id, section_id, deployment_name, use_underscore_names, dry_run):
    if dry_run:
        print('\n\n========= DRY RUN =========\n\n')
    if use_underscore_names:
        print('\nUsing old Dropbox folder naming format (underscores)\n')
    else:
        print('\nUsing new Dropbox folder naming format (replacing underscores with dashes)')
        print('To use old Dropbox folder naming format, append "--use-underscore-folder-names" to command\n')
    # get list of media ids in deployment
    print(f'Fetching media IDs for deployment {deployment_name} from Tator...', end='')
    sys.stdout.flush()
    media_ids = {}
    bottom_time = None
    camera_bottom_unix_timestamp = None
    res = requests.get(
        url=f'https://cloud.tator.io/rest/Medias/{project_id}?section={section_id}&attribute_contains=%24name%3A%3A{deployment_name}',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Token {TATOR_TOKEN}',
        })
    if res.status_code != 200:
        print(f'\n{TERM_RED}Error fetching media IDs: {res.json()["message"]}{TERM_NORMAL}')
        exit(1)
    full_media_list = res.json()
    for media in full_media_list:
        if not media['attributes'].get('Start Time'):
            print(f'Media {media["id"]} does not have a start timestamp')
            exit(1)
        media_ids[media['id']] = media['attributes']['Start Time']
        if media['attributes'].get('Arrival') and media['attributes']['Arrival'] != '':
            video_start_timestamp = datetime.fromisoformat(media['attributes']['Start Time'])
            if 'not observed' in media['attributes']['Arrival'].lower():
                bottom_time = video_start_timestamp
            else:
                bottom_time = video_start_timestamp + timedelta(seconds=int(int(media['attributes']['Arrival'].split('|')[0]) / 30))
            camera_bottom_unix_timestamp = time.mktime(bottom_time.timetuple())
    print(f'fetched {len(media_ids)} media IDs!')

    if bottom_time is None:
        print(f'{TERM_RED}No media with "arrival time" found in Tator for this deployment{TERM_NORMAL}')
        exit(1)

    # get all localizations in deployment
    print(f'Fetching localizations from Tator...', end='')
    sys.stdout.flush()
    localizations = []
    get_localization_res = requests.get(
        url=f'https://cloud.tator.io/rest/Localizations/{project_id}?media_id={",".join(map(str, media_ids.keys()))}',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Token {TATOR_TOKEN}',
        }
    )
    if res.status_code != 200:
        print(f'\n{TERM_RED}Error fetching localizations: {res.json()["message"]}{TERM_NORMAL}')
        exit(1)
    localizations += get_localization_res.json()
    print(f'fetched {len(localizations)} localizations!')
    print()

    # get the csv for the deployment
    print(f'Fetching CTD CSV file from Dropbox...', end='')
    sys.stdout.flush()
    dbx = dropbox.Dropbox(os.getenv('DROPBOX_ACCESS_TOKEN'))  # create a Dropbox client instance
    path = None
    df = None
    folder_path = f'{os.getenv("DROPBOX_FOLDER_PATH")}/{deployment_name if use_underscore_names else deployment_name.replace("_", "-")}/Sensor'
    try:
        # get the folder metadata
        folder_metadata = dbx.files_list_folder(folder_path)
        for entry in folder_metadata.entries:  # iterate over the entries in the folder
            if entry.name[0] == '.':
                continue
            path = os.path.join(folder_path, entry.name)
            if isinstance(entry, dropbox.files.FileMetadata) and entry.name[-3:].lower() == 'csv':
                # assume there is only one csv file in the sensor folder
                _, res = dbx.files_download(path)
                print('fetched!')
                print(f'Dropbox file location: {path}')
                df = pd.read_csv(res.raw)
                break
    except dropbox.exceptions.ApiError as e:
        print(f'\n{TERM_RED}Error connecting to Dropbox: {e}{TERM_NORMAL}')
        print(f'Tried looking for CSV sensor file in folder: {folder_path}')
        print('Is this the correct folder path?')
        exit(1)
    except dropbox.exceptions.AuthError as e:
        print(f'\n\n{TERM_RED}Error connecting to Dropbox: {e}{TERM_NORMAL}')
        exit(1)

    if df is None:
        print(f'\n{TERM_RED}No CTD CSV file found in Dropbox{TERM_NORMAL}')
        exit(1)

    for expected_col_header in [
        'Depth (meters)',
        'Dropcam Timestamp (s)',
        'DO Temperature (celsius)',
        'DO Concentration Salin Comp (mol/L)',
    ]:
        if expected_col_header not in df.keys():
            print(f'{TERM_RED}Sensor CSV not in expected format: Missing column with header "{expected_col_header}"{TERM_NORMAL}')
            print(f'See CSV file here: https://www.dropbox.com/home{path}')
            exit(1)

    df = df.rename(columns={
        'Depth (meters)': 'depth',
        'Dropcam Timestamp (s)': 'timestamp',
        'DO Temperature (celsius)': 'temp',
        'DO Concentration Salin Comp (mol/L)': 'o2_concentration',
    })
    df = df[['timestamp', 'depth', 'temp', 'o2_concentration']]

    before_length = len(df)

    # get rid of any rows with wonky timestamps
    first_timestamp = df['timestamp'][0]  # assume that the first timestamp is correct
    df = df[df['timestamp'] >= first_timestamp]
    df = df[df['timestamp'] < first_timestamp + 72 * 60 * 60]  # +72 hrs
    df = df.reset_index(drop=True)

    if before_length != len(df):
        print(f'\nRemoved {before_length - len(df)} rows with wonky timestamps')

    # find the point at which the depths stop increasing
    bottom_row = None
    depth = None
    rolling_avg = df['depth'].rolling(window=20).mean()
    for i in range(250, len(rolling_avg)):  # assuming it takes at least 250 seconds to reach the bottom
        diff = rolling_avg[i] - rolling_avg[i - 1]
        if abs(diff) < 0.1 and df['depth'][i] > 200:
            bottom_row = df.iloc[rolling_avg.index[i] - 20]
            depth = bottom_row['depth']
            break

    if bottom_row is None:
        print(f'{TERM_RED}Could not find bottom arrival time{TERM_NORMAL}')
        exit(1)

    print(f'\nCalculated bottom arrival time from sensor data (unix): {bottom_row["timestamp"]}')
    print(f'Recommend double-checking this timestamp in the CSV file ^^^^^^^^^^')

    offset = camera_bottom_unix_timestamp - bottom_row['timestamp']

    # parse time difference to hours, minutes, seconds
    delta_offset = timedelta(seconds=offset)
    print(f'\nOffset between camera time and sensor time: {int(offset)} seconds ({delta_offset})')

    bottom_df = df[df['depth'] > depth - 10]  # only the rows at bottom
    ascent_descent_df = df[df['depth'] <= depth - 10]  # ascent/descent rows

    # get the average of sensor data for the time that the camera was at the bottom
    avg_temp_at_bottom = bottom_df['temp'].mean()
    avg_o2_at_bottom = bottom_df['o2_concentration'].mean()

    # standard deviation of the sensor data for the time that the camera was at the bottom
    std_temp_at_bottom = bottom_df['temp'].std()
    std_do_o2_at_bottom = bottom_df['o2_concentration'].std()

    print(f'\nAvg temperature at bottom: {avg_temp_at_bottom.round(2)} ± {std_temp_at_bottom.round(2)}')
    print(f'Avg DO concentration at bottom: {avg_o2_at_bottom.round(2)} ± {std_do_o2_at_bottom.round(2)}')

    before_length = len(df)

    # remove any rows at bottom with a temperature diff that is greater than 3 standard deviations from the mean
    bottom_df = bottom_df[(bottom_df['temp'] - avg_temp_at_bottom).abs() < 3 * std_temp_at_bottom]
    # remove any rows at bottom with a do concentration diff that is greater than 3 standard deviations from the mean
    bottom_df = bottom_df[(bottom_df['o2_concentration'] - avg_o2_at_bottom).abs() < 3 * std_do_o2_at_bottom]

    df = pd.concat([bottom_df, ascent_descent_df])  # join the dataframes back together
    df = df.sort_values(by='timestamp')

    print(f'\nRemoved {before_length - len(df)} rows with outliers (> 3 std devs from the mean)')
    print('\nSyncing CTD data...')

    count_success = 0
    count_failure = 0
    count_interpolated = 0

    # for each localization, populate the DO Temperature and DO Concentration Salin Comp attributes
    for localization in localizations:
        # get the timestamp of the localization
        video_start_timestamp = datetime.fromisoformat(media_ids[localization['media']])
        this_timestamp = video_start_timestamp + timedelta(seconds=localization['frame'] / 30)
        unix_timestamp = time.mktime(this_timestamp.timetuple())
        # find the row in the CSV that matches the timestamp
        converted_timestamp = unix_timestamp - offset
        row = df.loc[df['timestamp'] == converted_timestamp]
        ctd_offset_seconds = 0
        if row.empty:  # missing this timestamp, get the closest row with an earlier timestamp
            filtered_df = df.loc[df['timestamp'] < converted_timestamp]
            if filtered_df.empty:
                print(f'{TERM_RED}No earlier timestamp found for localization {localization["elemental_id"]} '
                      f'(timestamp {converted_timestamp}), skipping{TERM_NORMAL}')
                continue
            row = filtered_df.iloc[-1]
            ctd_offset_seconds = converted_timestamp - row['timestamp']
            do_temp = row['temp']
            do_concentration = row['o2_concentration']
            depth = row['depth']
            count_interpolated += 1
        else:
            do_temp = row['temp'].values[0]
            do_concentration = row['o2_concentration'].values[0]
            depth = row['depth'].values[0]

        if do_temp <= 0 or do_temp > 35:
            print(f'{TERM_YELLOW}WARNING: DO Temperature out of range (0-35): {do_temp}{TERM_NORMAL}')
            print(f'Timestamp: {converted_timestamp}')
            print('Attempting to find row with a valid DO Temperature...')
            earlier_do_temp = -1
            later_do_temp = -1
            search_offset = 1
            while (earlier_do_temp <= 0 or earlier_do_temp > 35) and (later_do_temp <= 0 or later_do_temp > 35):
                row = df.loc[df['timestamp'] == converted_timestamp - search_offset]
                try:
                    earlier_do_temp = row['temp'].values[0]
                except IndexError:
                    pass
                if 0 < earlier_do_temp <= 35:
                    print(f'Found valid DO Temperature at timestamp {converted_timestamp - search_offset} ({search_offset} seconds earlier)')
                    do_temp = earlier_do_temp
                    do_concentration = row['o2_concentration'].values[0]
                    depth = row['depth'].values[0]
                    break
                row = df.loc[df['timestamp'] == converted_timestamp + search_offset]
                try:
                    later_do_temp = row['temp'].values[0]
                except IndexError:
                    pass
                if 0 < later_do_temp <= 35:
                    print(f'Found valid DO Temperature at timestamp {converted_timestamp + search_offset} ({search_offset} seconds later)')
                    do_temp = later_do_temp
                    do_concentration = row['o2_concentration'].values[0]
                    depth = row['depth'].values[0]
                    break
                search_offset += 1
                if search_offset > 300:
                    print(f'{TERM_RED}Could not find valid DO Temperature within 5 minutes of localization, exiting{TERM_NORMAL}')
                    exit(1)
        if do_concentration <= 0 or do_concentration > 320:
            print(f'{TERM_YELLOW}WARNING: DO Concentration out of range (0-320): {do_concentration}{TERM_NORMAL}')
            print(f'Timestamp: {converted_timestamp}')
            print('Attempting to find row with a valid DO Concentration...')
            earlier_do_concentration = -1
            later_do_concentration = -1
            search_offset = 1
            while (earlier_do_concentration <= 0 or earlier_do_concentration > 320) and (later_do_concentration <= 0 or later_do_concentration > 320):
                row = df.loc[df['timestamp'] == converted_timestamp - search_offset]
                try:
                    earlier_do_concentration = row['o2_concentration'].values[0]
                except IndexError:
                    pass
                if 0 < earlier_do_concentration <= 320:
                    print(f'Found valid DO Concentration at timestamp {converted_timestamp - search_offset} ({search_offset} seconds earlier)')
                    do_concentration = earlier_do_concentration
                    do_temp = row['temp'].values[0]
                    depth = row['depth'].values[0]
                    break
                row = df.loc[df['timestamp'] == converted_timestamp + search_offset]
                try:
                    later_do_concentration = row['o2_concentration'].values[0]
                except IndexError:
                    pass
                if 0 < later_do_concentration <= 320:
                    print(f'Found valid DO Concentration Salin Comp at timestamp {converted_timestamp + search_offset} ({search_offset} seconds later)')
                    do_concentration = earlier_do_concentration
                    do_temp = row['temp'].values[0]
                    depth = row['depth'].values[0]
                    break
                search_offset += 1
                if search_offset > 300:
                    print(f'{TERM_RED}Could not find valid DO Concentration Salin Comp within 5 minutes of localization, exiting{TERM_NORMAL}')
                    exit(1)
        if depth + 50 < bottom_row['depth']:
            print(f'{TERM_YELLOW}WARNING: Unexpected depth: {depth} (deployment depth was approximately {bottom_row["depth"]}){TERM_NORMAL}')
            print(f'Localization URL: https://cloud.tator.io/{project_id}/annotation/{localization["media"]}?frame={localization["frame"]}')
            print(f'Sensor timestamp: {converted_timestamp}')

        attributes = {
            'DO Temperature (celsius)': do_temp,
            'DO Concentration Salin Comp (mol per L)': do_concentration,
            'Depth': depth,
        }
        if ctd_offset_seconds > 0:
            data_note = f'Temperature and oxygen data collected {round(ctd_offset_seconds)} ' \
                        f'second{"s" if ctd_offset_seconds > 1 else ""} before timestamp of record'
            current_notes = localization['attributes'].get('Notes')
            if current_notes and current_notes != '':
                note_parts = current_notes.split('|')
                note_parts = [part for part in note_parts if 'Temperature and oxygen data collected' not in part]
                note_parts.append(data_note)
                attributes['Notes'] = '|'.join(note_parts)
            else:
                attributes['Notes'] = data_note

        if dry_run:
            print(attributes)
        else:
            # update the localization
            update_res = requests.patch(
                url=f'https://cloud.tator.io/rest/Localization/{localization["id"]}',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Token {TATOR_TOKEN}',
                },
                json={'attributes': attributes},
            )
            if update_res.status_code == 200:
                count_success += 1
                print(update_res.json().get('message'))
            else:
                count_failure += 1
                print(f'{TERM_RED}{update_res.json().get("message")}{TERM_NORMAL}')

    # pau
    marine_emojis = ['🦈', '🐠', '🐬', '🐋', '🐙', '🦑', '🦐', '🦞', '🦀', '🐚', '🌊']
    print()
    print(f'{TERM_GREEN}Successfully populated CTD for {count_success} localizations{TERM_NORMAL}')
    if count_interpolated > 0:
        print(f'Of those, {count_interpolated} used a previous timestamp...', end='')
        sys.stdout.flush()
        # get all deployment notes
        deployment_notes = set()
        for media in full_media_list:
            media_deployment_notes = media['attributes'].get('Deployment Notes')
            if media_deployment_notes and media_deployment_notes != '':
                deployment_notes.add(media['attributes']['Deployment Notes'])
        deployment_notes.add('Temperature and oxygen sensor readings intermittent')
        if dry_run:
            print({'Deployment Notes': '|'.join(deployment_notes)})
        else:
            update_res = requests.patch(
                url=f'https://cloud.tator.io/rest/Medias/{project_id}?media_id={",".join(map(str, media_ids.keys()))}',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Token {TATOR_TOKEN}',
                },
                json={'attributes': {'Deployment Notes': '|'.join(deployment_notes)}},
            )
            if update_res.status_code == 200:
                print('added wonky sensor data note to "Deployment Notes"!')
            else:
                print(f'{TERM_RED}{update_res.json().get("message")}{TERM_NORMAL}')
    if count_failure > 0:
        print(f'{TERM_RED}Failed to populate CTD for {count_failure} localizations{TERM_NORMAL}')
    print()
    print(f'{deployment_name} complete {marine_emojis[count_success % len(marine_emojis)]}')
    print()


dotenv.load_dotenv()
TATOR_TOKEN = os.getenv('TATOR_TOKEN')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Syncs CTD data from Dropbox to Tator')
    parser.add_argument('project_id', type=int, help='Tator project ID (most likely 26)')
    parser.add_argument('section_id', type=int, help='Tator section ID (e.g. 18641)')
    parser.add_argument('deployment_name', type=str, help='Name of the deployment (e.g. PNG_dscm_01)')
    parser.add_argument('--use-underscore-folder-names', action='store_true', help='Use old Dropbox folder naming format (underscores)')
    parser.add_argument('--dry-run', action='store_true', help='Do not update Tator, just print the changes (for development)')
    args = parser.parse_args()
    populate_ctd(
        project_id=args.project_id,
        section_id=args.section_id,
        deployment_name=args.deployment_name,
        use_underscore_names=args.use_underscore_folder_names,
        dry_run=args.dry_run,
    )
    os.system('say "Deployment CTD synced."')
