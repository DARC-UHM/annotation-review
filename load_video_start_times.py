"""
Populates the 'Start Time' attribute of videos in Tator with the creation date of the video file.
Creation date is extracted from the XML metadata of the video file in Dropbox.

To run this script, you must have a .env file in the same directory as this script with the following variables:
    - DROPBOX_ACCESS_TOKEN: Access token for the Dropbox API (https://www.dropbox.com/developers/apps)
    - DROPBOX_FOLDER_PATH: Path to the folder in Dropbox containing the deployment's video files
    - TATOR_TOKEN: Tator API token

Usage: python load_video_start_times.py <project_id> <section_id> <deployment_name>
"""

import dropbox
import os
import requests
import xml.etree.ElementTree as ET
import sys
import dotenv


def process_folder(folder_path):
    # Create a Dropbox client instance
    dbx = dropbox.Dropbox(os.getenv('DROPBOX_ACCESS_TOKEN'))
    try:
        # Get the folder metadata
        folder_metadata = dbx.files_list_folder(folder_path)

        # Iterate over the entries in the folder
        for entry in folder_metadata.entries:
            path = os.path.join(folder_path, entry.name)

            # If the entry is a file, download and print its contents
            if isinstance(entry, dropbox.files.FileMetadata) and entry.name[-3:] == 'xml':
                _, res = dbx.files_download(path)
                print(path)
                xml_content = res.content.decode('utf-8')
                root = ET.fromstring(xml_content)
                creation_date = root.find('.//{urn:schemas-professionalDisc:nonRealTimeMeta:ver.2.00}CreationDate').attrib['value']
                media_list[path.split('/')[-1][:-4]]['creation_date'] = creation_date

            # If the entry is a folder, recursively process its contents
            elif isinstance(entry, dropbox.files.FolderMetadata):
                process_folder(path)

    except dropbox.exceptions.ApiError as e:
        print(f'Error: {e}')


def get_tator_media_ids(project_id, section_id, tator_token):
    req = requests.get(
        f'https://cloud.tator.io/rest/Medias/{project_id}?section={section_id}',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Token {tator_token}',
        })
    for media in req.json():
        media_name = media['name'].split('_')
        # until we decide on an actual naming convention...
        if len(media_name) == 3:  # format DOEX0087_NIU-dscm-02_c009.mp4
            media_list[f'{media_name[1]}_{media_name[2]}'] = {'id': media['id']}
        else:  # format HAW_dscm_01_c010_202304250123Z_0983m.mp4
            media_list[f'{media_name[0]}_{media_name[1]}_{media_name[2]}_{media_name[3]}'] = {'id': media['id']}
    print('Retrieved media ids from Tator')


def set_video_start_time(media_id, start_time, tator_token):
    data = {
        'attributes': {
            'Start Time': start_time,
        },
    }
    req = requests.patch(
        f'https://cloud.tator.io/rest/Media/{media_id}',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Token {tator_token}',
        },
        json=data)
    print(req.json())


if len(sys.argv) != 4:
    print('Usage: python load_video_start_times.py <project_id> <section_id> <deployment_name>')
    sys.exit()

dotenv.load_dotenv()

TATOR_TOKEN = os.getenv('TATOR_TOKEN')
PROJECT_ID = sys.argv[1]
SECTION_ID = sys.argv[2]
DEPLOYMENT_NAME = sys.argv[3]

media_list = {}

get_tator_media_ids(
    project_id=PROJECT_ID,
    section_id=SECTION_ID,
    tator_token=TATOR_TOKEN,
)
process_folder(folder_path=f'{os.getenv("DROPBOX_FOLDER_PATH")}/{DEPLOYMENT_NAME}')
for media in media_list.values():
    if 'creation_date' in media.keys():
        set_video_start_time(
            media_id=media['id'],
            start_time=media['creation_date'],
            tator_token=TATOR_TOKEN,
        )

print(f'{DEPLOYMENT_NAME} complete!')
