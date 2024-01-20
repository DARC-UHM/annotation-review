import requests
import pandas as pd
import tator

from flask import session
from .functions import *

TATOR_URL = 'https://cloud.tator.io'
TERM_RED = '\033[1;31;48m'
TERM_NORMAL = '\033[1;37;0m'


class LocalizationProcessor:
    """
    Fetches all localization information for a given project/section from Tator. Processes and sorts data for display
    on the image review pages.
    """

    def __init__(self, project_id: int, section_id: int):
        self.project_id = project_id
        self.section_id = section_id
        self.deployment_list = set()
        self.media_list = {}
        self.distilled_records = []
        self.api = tator.get_api(
            host=TATOR_URL,
            token=session['tator_token'],
        )
        self.section_name = self.api.get_section(self.section_id).name
        self.load_media()
        self.load_localizations()

    def load_media(self):
        print('Loading media...', end='')
        for media in self.api.get_media_list(project=self.project_id, section=self.section_id):
            self.media_list[media.id] = media.name
            self.deployment_list.add(media.name[:11])
        for media in self.media_list:
            print(media, self.media_list[media])
        for deployment in self.deployment_list:
            print(deployment)
        print('done!')

    def load_localizations(self):
        print('Loading localizations...', end='')
        localizations = self.api.get_localization_list(
            project=self.project_id,
            section=self.section_id,
            start=0,
            stop=10,  # todo remove
        )
        self.distilled_records = [
            {
                'id': localization.id,
                'type': localization.type,  # 48 = box, 49 = dot (for now?)
                'media': localization.media,
                'frame': localization.frame,
                'attributes': localization.attributes,
                'created_by': localization.created_by,
                'x': localization.x,
                'y': localization.y,
                'image_url': f'/tator-image/{localization.id}',
                'frame_url': f'/tator-frame/{localization.media}/{localization.frame}',
            }
            for localization in localizations
        ]
        print('done!')

    def load_images(self, name: str):
        print(f'Fetching annotations for sequence {name} from VARS...', end='')
        concept_phylogeny = {'Animalia': {}}
        image_records = []
        videos = []

        with requests.get(f'http://hurlstor.soest.hawaii.edu:8086/query/dive/{name.replace(" ", "%20")}') as r:
            response = r.json()
            print('fetched!')
        print('Processing annotations...', end='')
        # get list of video links and start timestamps
        for video in response['media']:
            if 'urn:imagecollection:org' not in video['uri']:
                videos.append([parse_datetime(video['start_timestamp']),
                               video['uri'].replace('http://hurlstor.soest.hawaii.edu/videoarchive',
                                                    'https://hurlvideo.soest.hawaii.edu')])

        video_sequence_name = response['media'][0]['video_sequence_name']

