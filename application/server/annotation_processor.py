import json
import os
import sys

import requests
import pandas as pd

from .functions import *

TERM_RED = '\033[1;31;48m'
TERM_NORMAL = '\033[1;37;0m'


class AnnotationProcessor:
    """
    Fetches annotation information from the VARS db on HURLSTOR given a list of sequences. Cleans, formats, and sorts
    the annotation data for display on the image review pages.
    """

    def __init__(self, sequence_names: list):
        self.sequence_names = sequence_names
        self.phylogeny = {}
        self.image_records = []
        self.distilled_records = []
        temp_name = sequence_names[0].split()
        temp_name.pop()
        self.vessel_name = ' '.join(temp_name)

    def process_sequences(self):
        self.load_phylogeny()
        sequence_videos = []
        for name in self.sequence_names:
            print(f'Fetching annotations for sequence {name} from VARS...', end='')
            sys.stdout.flush()
            self.fetch_media(name, sequence_videos)
            print('fetched!')
        print('Processing annotations...', end='')
        sys.stdout.flush()
        self.sort_records(self.process_images(sequence_videos))
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

    def fetch_media(self, sequence_name: str, sequence_videos: list):
        """
        Fetches all annotations that have images and all video uris/start times from VARS.
        """
        response = requests.get(f'http://hurlstor.soest.hawaii.edu:8086/query/dive/{sequence_name.replace(" ", "%20")}').json()

        # get list of video links and start timestamps
        for video in response['media']:
            if 'urn:imagecollection:org' not in video['uri']:
                video_uri = video['uri'].replace('http://hurlstor.soest.hawaii.edu/videoarchive','https://hurlvideo.soest.hawaii.edu')
                sequence_videos.append({
                    'start_timestamp': parse_datetime(video['start_timestamp']),
                    'uri': video_uri,
                    'sequence_name': video['video_sequence_name'],
                })
        # get all annotations that have images
        for annotation in response['annotations']:
            concept_name = annotation['concept']
            if annotation['image_references'] and concept_name[0].isupper():
                self.image_records.append(annotation)

    def fetch_vars_phylogeny(self, concept_name: str):
        """
        Fetches phylogeny for given concept from the VARS knowledge base.
        """
        vars_tax_res = requests.get(f'http://hurlstor.soest.hawaii.edu:8083/kb/v1/phylogeny/up/{concept_name}')
        if vars_tax_res.status_code == 200:
            # this get us to phylum
            try:
                vars_tree = vars_tax_res.json()['children'][0]['children'][0]['children'][0]['children'][0]['children'][0]
                self.phylogeny[concept_name] = {}
            except KeyError:
                print(f'\n{TERM_RED}VARS phylogeny for {concept_name} not in expected format{TERM_NORMAL}')
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
        image_url = annotation['image_references'][0]['url']
        for i in range(1, len(annotation['image_references'])):
            if '.png' in annotation['image_references'][i]['url']:
                image_url = annotation['image_references'][i]['url']
                break
        return image_url.replace('http://hurlstor.soest.hawaii.edu/imagearchive', 'https://hurlimage.soest.hawaii.edu')

    def get_video_url(self, annotation: dict, sequence_videos: list) -> dict:
        """
        Gets the video url and sequence name for the given annotation record. Selects the video from the list of
        sequence videos that contains the annotation and adds offset to the video url.
        """
        if 'recorded_timestamp' not in annotation.keys():
            return {}
        timestamp = parse_datetime(annotation['recorded_timestamp'])
        matching_video = sequence_videos[0]
        for video in sequence_videos:
            if video['start_timestamp'] > timestamp:
                break
            matching_video = video
        time_diff = timestamp - matching_video['start_timestamp']
        matching_video['uri'] = f'{matching_video["uri"]}#t={int(time_diff.total_seconds())}'
        return matching_video

    def process_images(self, sequence_videos: list):
        """
        Cleans and formats the image records into a list of dicts.
        """
        formatted_images = []

        for record in self.image_records:
            concept_name = record['concept']
            if concept_name not in self.phylogeny.keys():
                self.fetch_vars_phylogeny(concept_name)

            annotation_dict = {
                'observation_uuid': record['observation_uuid'],
                'concept': concept_name,
                'identity_certainty': get_association(record, 'identity-certainty')['link_value'] if get_association(record, 'identity-certainty') else None,
                'identity_reference': get_association(record, 'identity-reference')['link_value'] if get_association(record, 'identity-reference') else None,
                'guide_photo': get_association(record, 'guide-photo')['to_concept'] if get_association(record, 'guide-photo') else None,
                'comment': get_association(record, 'comment')['link_value'] if get_association(record, 'comment') else None,
                'image_url': self.get_image_url(record),
                'video_url': self.get_video_url(record, sequence_videos).get('uri'),
                'upon': get_association(record, 'upon')['to_concept'] if get_association(record, 'upon') else None,
                'recorded_timestamp': record['recorded_timestamp'],
                'video_sequence_name': self.get_video_url(record, sequence_videos).get('sequence_name'),
                'annotator': format_annotator(record['observer']),
                'depth': int(record['ancillary_data']['depth_meters']) if 'ancillary_data' in record.keys() and 'depth_meters' in record['ancillary_data'].keys() else None,
                'lat': round(record['ancillary_data']['latitude'], 3) if 'ancillary_data' in record.keys() and 'latitude' in record['ancillary_data'].keys() else None,
                'long': round(record['ancillary_data']['longitude'], 3) if 'ancillary_data' in record.keys() and 'longitude' in record['ancillary_data'].keys() else None,
                'temperature': round(record['ancillary_data']['temperature_celsius'], 2) if 'ancillary_data' in record.keys() and 'temperature_celsius' in record['ancillary_data'].keys() else None,
                'oxygen_ml_l': round(record['ancillary_data']['oxygen_ml_l'], 3) if 'ancillary_data' in record.keys() and 'oxygen_ml_l' in record['ancillary_data'].keys() else None,
            }

            if concept_name in self.phylogeny.keys():
                for key in self.phylogeny[concept_name].keys():
                    annotation_dict[key] = self.phylogeny[concept_name][key]
            formatted_images.append(annotation_dict)

        return formatted_images

    def sort_records(self, formatted_images: list):
        """
        Uses pandas to sort the formatted images by phylogeny and other attributes. Adds the sorted records to the
        distilled records list.
        """
        annotation_df = pd.DataFrame(formatted_images, columns=[
            'observation_uuid',
            'concept',
            'identity_certainty',
            'identity_reference',
            'guide_photo',
            'comment',
            'image_url',
            'video_url',
            'upon',
            'recorded_timestamp',
            'video_sequence_name',
            'annotator',
            'depth',
            'lat',
            'long',
            'temperature',
            'oxygen_ml_l',
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
            'identity_certainty',
            'recorded_timestamp',
        ])

        annotation_df = annotation_df.replace({float('nan'): None})

        for index, row in annotation_df.iterrows():
            self.distilled_records.append({
                'observation_uuid': row['observation_uuid'],
                'concept': row['concept'],
                'annotator': row['annotator'],
                'depth': row['depth'],
                'lat': row['lat'],
                'long': row['long'],
                'temperature': row['temperature'],
                'oxygen_ml_l': row['oxygen_ml_l'],
                'phylum': row['phylum'],
                'class': row['class'],
                'order': row['order'],
                'family': row['family'],
                'genus': row['genus'],
                'species': row['species'],
                'identity_certainty': row['identity_certainty'],
                'identity_reference': row['identity_reference'],
                'guide_photo': row['guide_photo'],
                'comment': row['comment'],
                'image_url': row['image_url'],
                'video_url': row['video_url'],
                'upon': row['upon'],
                'recorded_timestamp': parse_datetime(row['recorded_timestamp']).strftime('%d %b %y %H:%M:%S UTC'),
                'video_sequence_name': row['video_sequence_name'],
            })
