"""
===================================================================================================

NOTE: THIS SCRIPT SHOULD NO LONGER BE NECESSARY AS START TIMES SHOULD BE AUTOMATICALLY BE POPULATED
FROM THE XML METADATA FILES WHEN THE MEDIA CLIPS ARE FIRST UPLOADED INTO TATOR.

===================================================================================================

Populates the 'Start Time' attribute of videos in Tator with the creation date of the video file.
Creation date is extracted from the XML metadata of the video file in Dropbox.

To run this script, you must have a .env file in the root of the repository with the following variables:
    - DROPBOX_ACCESS_TOKEN: Access token for the Dropbox API (https://www.dropbox.com/developers/apps)
    - DROPBOX_FOLDER_PATH: Path to the folder in Dropbox containing the deployment's video files
    - TATOR_TOKEN: Tator API token

Usage: python load_video_start_times.py <project_id> <section_id> <deployment_name> [--use-underscore-folder-names]
"""

import dropbox
import os
import requests
import xml.etree.ElementTree as ET
import sys
import dotenv


def get_tator_media_ids(project_id, section_id, deployment_name, tator_token) -> int:
    if not tator_token:
        print('Error: Tator token not found')
        sys.exit()
    res = requests.get(
        f'https://cloud.tator.io/rest/Medias/{project_id}?section={section_id}&attribute_contains=%24name%3A%3A{deployment_name}',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Token {tator_token}',
        })
    if res.status_code != 200:
        print(f'Error connecting to Tator: {res.json()["message"]}')
        exit(1)
    for media in res.json():
        media_name = media['name'].split('_')
        # until we decide on an actual naming convention...
        if len(media_name) == 3:  # format DOEX0087_NIU-dscm-02_c009.mp4
            media_list[f'{media_name[1]}_{media_name[2]}'[:-4]] = {'id': media['id']}
        elif len(media_name) == 4:  # format PLW_dscm_02_c001.mp4  (the best one)
            media_list[media['name'].split('.')[0]] = {'id': media['id']}
        else:  # format HAW_dscm_01_c010_202304250123Z_0983m.mp4
            media_list[f'{media_name[0]}_{media_name[1]}_{media_name[2]}_{media_name[3]}'] = {'id': media['id']}
    return len(res.json())


def process_folder(folder_path):
    # Create a Dropbox client instance
    dbx = dropbox.Dropbox(os.getenv('DROPBOX_ACCESS_TOKEN'))
    xml_file_count = 0
    try:
        # Get the folder metadata
        folder_metadata = dbx.files_list_folder(folder_path)

        # Iterate over the entries in the folder
        for entry in folder_metadata.entries:
            path = os.path.join(folder_path, entry.name)

            # If the entry is a file, download and print its contents
            if isinstance(entry, dropbox.files.FileMetadata) and entry.name[-3:].lower() == 'xml':
                _, res = dbx.files_download(path)
                print(path)
                xml_content = res.content.decode('utf-8')
                root = ET.fromstring(xml_content)
                creation_date = root.find('.//{urn:schemas-professionalDisc:nonRealTimeMeta:ver.2.00}CreationDate').attrib['value']
                media_list[path.split('/')[-1][:-4]]['creation_date'] = creation_date
                xml_file_count += 1

            # If the entry is a folder, recursively process its contents
            elif isinstance(entry, dropbox.files.FolderMetadata):
                xml_file_count += process_folder(path)

        return xml_file_count

    except dropbox.exceptions.ApiError as e:
        print(f'Error connecting to Dropbox: {e}')
        print(f'Tried looking for XML files in folder: {folder_path}')
        print('Is this the correct folder path?')
        exit(1)


"""
This was to rename all the files in a folder when the were named incorrectly. Keeping this just 
in case we need to do something like this again in the future.

def change_names(folder_path):
    # change all file names in a folder to a new name
    dbx = dropbox.Dropbox(os.getenv('DROPBOX_ACCESS_TOKEN'))
    try:
        files = dbx.files_list_folder(f'{folder_path}/Video').entries
        for file_entry in files:
            old_path = file_entry.path_display
            old_name = file_entry.name
            new_name = old_name.replace('PLW_dscm_30', 'PLW_dscm_29')
            new_path = f'{folder_path}/Video/{new_name}'
            dbx.files_move_v2(old_path, new_path)
            print(f"File renamed: {old_name} -> {new_name}")
    except dropbox.exceptions.ApiError as e:
        print(f"Dropbox API error occurred: {e}")
"""


def set_video_start_time(media_id, start_time, tator_token):
    data = {
        'attributes': {
            'Start Time': start_time,
        },
    }
    res = requests.patch(
        f'https://cloud.tator.io/rest/Media/{media_id}',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Token {tator_token}',
        },
        json=data)
    print(res.json())


if len(sys.argv) not in [4, 5]:
    print('Usage: python load_video_start_times.py <project_id> <section_id> <deployment_name> [--use-underscore-folder-names]')
    sys.exit()

dotenv.load_dotenv()

TATOR_TOKEN = os.getenv('TATOR_TOKEN')
PROJECT_ID = sys.argv[1]
SECTION_ID = sys.argv[2]
DEPLOYMENT_NAME = sys.argv[3]

dropbox_folder_deployment_name = DEPLOYMENT_NAME

if len(sys.argv) == 5 and sys.argv[4] == '--use-underscore-folder-names':
    print('Using old Dropbox folder naming format (underscores)')
else:
    print('Using new Dropbox folder naming format (replacing underscores with dashes)')
    print('To use old Dropbox folder naming format, append "--use-underscore-folder-names" to command')
    dropbox_folder_deployment_name = dropbox_folder_deployment_name.replace("_", "-")

media_list = {}

print(f'Fetching media data for deployment {DEPLOYMENT_NAME} from Tator...', end='')
total_media_ids = get_tator_media_ids(
    project_id=PROJECT_ID,
    section_id=SECTION_ID,
    deployment_name=DEPLOYMENT_NAME,
    tator_token=TATOR_TOKEN,
)
print(f'fetched data for {total_media_ids} media files!')

print(f'Fetching video metadata XML files from DropBox...')
total_xml_files = process_folder(
    folder_path=f'{os.getenv("DROPBOX_FOLDER_PATH")}/{dropbox_folder_deployment_name}'
)
print(f'Fetched {total_xml_files} video metadata XML files!')

print(f'Populating start times in Tator for {total_media_ids} media files...')
total_media_updated = 0
for media in media_list.values():
    if 'creation_date' in media.keys():
        set_video_start_time(
            media_id=media['id'],
            start_time=media['creation_date'],
            tator_token=TATOR_TOKEN,
        )
        total_media_updated += 1
    else:
        print(f'Error: No creation date found for {media}')
print('Done populating start times in Tator!')
print()
print(f'Number media IDS: {total_media_ids}')
print(f'Number XML files: {total_xml_files}')
print(f'Number media updated: {total_media_updated}')
print(f'{DEPLOYMENT_NAME} complete!')
os.system('say "Start times synced."')
