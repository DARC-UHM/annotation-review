"""
Prints all the transect media IDs given an expedition name and a file containing a list of media names separated
by a newline.

Usage: python get_transect_media_ids.py <expedition-name> <file-containing-media-names>

Example: python get_transect_media_ids.py TUV_2025 media_names.txt
"""

import os

import dotenv
import sys

from tator_script_helper_functions import get_transect_media_ids

TATOR_REST_URL = 'https://cloud.tator.io/rest'

if len(sys.argv) != 3:
    print('Usage: python get_transect_media_ids.py <expedition-name> <file-containing-media-names>')
    exit(1)

dotenv.load_dotenv()

EXPEDITION_NAME = sys.argv[1]
FILE_NAME = sys.argv[2]
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'Token {os.getenv("TATOR_TOKEN")}',
}

with open(FILE_NAME) as f:
    MEDIA_NAMES = f.read().strip().split('\n')

for media_name, media_id in get_transect_media_ids(
    expedition_name=EXPEDITION_NAME,
    media_names=MEDIA_NAMES,
    tator_token=os.getenv('TATOR_TOKEN'),
).items():
    print(media_name, media_id)
