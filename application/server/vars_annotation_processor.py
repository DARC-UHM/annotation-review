import json
import os
import pandas as pd
import requests
import sys

from .functions import *
from .constants import TERM_RED, TERM_YELLOW, TERM_NORMAL


class VarsAnnotationProcessor:
    """
    Fetches annotation information from the VARS db on HURLSTOR given a list of sequences. Cleans, formats, and sorts
    the annotation data for display on the image review pages.
    """

    def __init__(self, sequence_names: list):
        self.sequence_names = sequence_names
        self.phylogeny = {}
        self.working_records = []  # all of the annotations that have images
        self.final_records = []    # the final list of annotations
        self.highest_id_ref = 0
        temp_name = sequence_names[0].split()
        temp_name.pop()
        self.vessel_name = ' '.join(temp_name)

    def process_sequences(self):
        self.load_phylogeny()
        videos = []
        for name in self.sequence_names:
            print(f'Fetching annotations for sequence {name} from VARS...', end='')
            sys.stdout.flush()
            self.fetch_media(name, videos)
            print('fetched!')
        print('Processing annotations...', end='')
        sys.stdout.flush()
        self.sort_records(self.process_working_records(videos))
        print('done!')
        self.save_phylogeny()

    def load_phylogeny(self):
        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'r') as f:
                self.phylogeny = json.load(f)
        except FileNotFoundError:
            self.phylogeny = {'Animalia': {}}

    def save_phylogeny(self):
        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(self.phylogeny, f, indent=2)
        except FileNotFoundError:
            os.makedirs('cache')
        with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
            json.dump(self.phylogeny, f, indent=2)

    def fetch_media(self, sequence_name: str, videos: list):
        """
        Fetches all annotations that have images and all video uris/start times from VARS.
        """
        response = requests.get(url=f'http://hurlstor.soest.hawaii.edu:8086/query/dive/{sequence_name.replace(" ", "%20")}').json()

        # get list of video links and start timestamps
        for video in response['media']:
            if 'urn:imagecollection:org' not in video['uri']:
                videos.append({
                    'start_timestamp': parse_datetime(video['start_timestamp']),
                    'uri': video['uri'].replace('http://hurlstor.soest.hawaii.edu/videoarchive', 'https://hurlvideo.soest.hawaii.edu'),
                    'sequence_name': video['video_sequence_name'],
                    'video_reference_uuid': video['video_reference_uuid'],
                })
        # get all annotations that have images
        for annotation in response['annotations']:
            concept_name = annotation['concept']
            if annotation['image_references'] and concept_name[0].isupper():
                self.working_records.append(annotation)

    def fetch_vars_phylogeny(self, concept_name: str, no_match_records: set):
        """
        Fetches phylogeny for given concept from the VARS knowledge base.
        """
        vars_tax_res = requests.get(url=f'http://hurlstor.soest.hawaii.edu:8083/v1/phylogeny/up/{concept_name}')
        if vars_tax_res.status_code == 200:
            try:
                # this get us to phylum
                vars_tree = vars_tax_res.json()['children'][0]['children'][0]['children'][0]['children'][0]['children'][0]
                self.phylogeny[concept_name] = {}
            except KeyError:
                if concept_name not in no_match_records:
                    no_match_records.add(concept_name)
                    print(f'{TERM_YELLOW}WARNING: Could not find phylogeny for concept "{concept_name}" in VARS knowledge base{TERM_NORMAL}')
                vars_tree = {}
            while 'children' in vars_tree.keys():
                if 'rank' in vars_tree.keys():  # sometimes it's not
                    self.phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                vars_tree = vars_tree['children'][0]
            if 'rank' in vars_tree.keys():
                self.phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
        else:
            print(f'\n{TERM_RED}Unable to find record for {concept_name}{TERM_NORMAL}')

    def get_image_url(self, annotation: dict) -> str:
        """
        Gets the correct image url from the given annotation record. Preferentially selects a png image if available
        (higher quality).
        """
        if len(annotation['image_references']) == 0:
            return ''
        image_url = annotation['image_references'][0]['url']
        for i in range(1, len(annotation['image_references'])):
            if '.png' in annotation['image_references'][i]['url']:
                image_url = annotation['image_references'][i]['url']
                break
        return image_url.replace('http://hurlstor.soest.hawaii.edu/imagearchive', 'https://hurlimage.soest.hawaii.edu')

    def get_video(self, annotation: dict, videos: list) -> dict:
        """
        Gets the video url and sequence name for the given annotation record. Selects the video from the list of
        sequence videos that contains the annotation and adds offset to the video url.
        """
        if 'recorded_timestamp' not in annotation.keys():
            return {}
        timestamp = parse_datetime(annotation['recorded_timestamp'])
        matching_video = videos[0]  # default to first video
        for video in videos:
            if video['start_timestamp'] > timestamp:
                break
            matching_video = video
        time_diff = timestamp - matching_video['start_timestamp']
        return {
            'uri': f'{matching_video["uri"]}#t={int(time_diff.total_seconds())}',
            'sequence_name': matching_video['sequence_name'],
        }

    def process_working_records(self, videos: list):
        """
        Cleans and formats the working records into a list of dicts.
        """
        formatted_records = []
        no_match_records = set()

        for record in self.working_records:
            concept_name = record['concept']
            identity_reference = None
            depth = None
            lat = None
            long = None
            temperature = None
            oxygen_ml_l = None

            if concept_name not in self.phylogeny.keys() and concept_name != 'none':
                self.fetch_vars_phylogeny(concept_name, no_match_records)

            video = self.get_video(record, videos)

            if record.get('associations'):
                for association in record['associations']:
                    if association['link_name'] == 'identity-reference':
                        identity_reference = association['link_value']
                        if int(identity_reference) > self.highest_id_ref:
                            self.highest_id_ref = int(identity_reference)
                        break

            if record.get('ancillary_data'):
                for key in record['ancillary_data'].keys():
                    if key == 'depth_meters':
                        depth = int(record['ancillary_data']['depth_meters'])
                    elif key == 'latitude':
                        lat = round(record['ancillary_data']['latitude'], 3)
                    elif key == 'longitude':
                        long = round(record['ancillary_data']['longitude'], 3)
                    elif key == 'temperature_celsius':
                        temperature = round(record['ancillary_data']['temperature_celsius'], 2)
                    elif key == 'oxygen_ml_l':
                        oxygen_ml_l = round(record['ancillary_data'][key], 3)

            annotation_dict = {
                'observation_uuid': record['observation_uuid'],
                'concept': concept_name,
                'associations': record['associations'],
                'identity_reference': identity_reference,
                'image_url': self.get_image_url(record),
                'video_url': video.get('uri'),
                'recorded_timestamp': record['recorded_timestamp'],
                'video_sequence_name': video.get('sequence_name'),
                'annotator': format_annotator(record['observer']),
                'activity': record['activity'] if 'activity' in record.keys() else None,
                'depth': depth,
            }

            if concept_name in self.phylogeny.keys():
                for key in self.phylogeny[concept_name].keys():
                    # split to account for worms 'Phylum (Division)' case
                    annotation_dict[key.split(' ')[0]] = self.phylogeny[concept_name][key]
            formatted_records.append(annotation_dict)
        return formatted_records

    def sort_records(self, formatted_records: list):
        """
        Uses pandas to sort the formatted images by phylogeny and other attributes. Adds the sorted records to the
        distilled records list.
        """
        annotation_df = pd.DataFrame(formatted_records, columns=[
            'observation_uuid',
            'concept',
            'associations',
            'identity_reference',
            'image_url',
            'video_url',
            'recorded_timestamp',
            'video_sequence_name',
            'annotator',
            'activity',
            'depth',
            'phylum',
            'subphylum',
            'superclass',
            'class',
            'subclass',
            'superorder',
            'order',
            'suborder',
            'infraorder',
            'superfamily',
            'family',
            'subfamily',
            'genus',
            'species',
        ])

        annotation_df = annotation_df.sort_values(by=[
            'phylum',
            'subphylum',
            'superclass',
            'class',
            'subclass',
            'superorder',
            'order',
            'suborder',
            'infraorder',
            'superfamily',
            'family',
            'subfamily',
            'genus',
            'species',
            'concept',
            'identity_reference',
            'recorded_timestamp',
        ])

        annotation_df = annotation_df.replace({float('nan'): None})

        for index, row in annotation_df.iterrows():
            self.final_records.append({
                'observation_uuid': row['observation_uuid'],
                'concept': row['concept'],
                'associations': row['associations'],
                'activity': row['activity'],
                'annotator': row['annotator'],
                'depth': row['depth'],
                'phylum': row['phylum'],
                'class': row['class'],
                'order': row['order'],
                'family': row['family'],
                'genus': row['genus'],
                'species': row['species'],
                'identity_reference': row['identity_reference'],
                'image_url': row['image_url'],
                'video_url': row['video_url'],
                'recorded_timestamp': parse_datetime(row['recorded_timestamp']).strftime('%d %b %y %H:%M:%S UTC'),
                'video_sequence_name': row['video_sequence_name'],
            })
