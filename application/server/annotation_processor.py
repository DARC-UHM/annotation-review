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
        self.distilled_records = []
        temp_name = sequence_names[0].split()
        temp_name.pop()
        self.vessel_name = ' '.join(temp_name)
        for name in sequence_names:
            self.load_images(name)

    def load_images(self, name: str):
        print(f'Fetching annotations for sequence {name} from VARS...', end='')
        sys.stdout.flush()
        image_records = []
        videos = []

        with requests.get(f'http://hurlstor.soest.hawaii.edu:8086/query/dive/{name.replace(" ", "%20")}') as r:
            response = r.json()
            print('fetched!')
        print('Processing annotations...', end='')
        sys.stdout.flush()
        # get list of video links and start timestamps
        for video in response['media']:
            if 'urn:imagecollection:org' not in video['uri']:
                videos.append([parse_datetime(video['start_timestamp']),
                               video['uri'].replace('http://hurlstor.soest.hawaii.edu/videoarchive',
                                                    'https://hurlvideo.soest.hawaii.edu')])

        video_sequence_name = response['media'][0]['video_sequence_name']

        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'r') as f:
                phylogeny = json.load(f)
        except FileNotFoundError:
            phylogeny = {'Animalia': {}}

        # Get all of the annotations that have images
        for annotation in response['annotations']:
            concept_name = annotation['concept']
            if annotation['image_references'] and concept_name[0].isupper():
                image_records.append(annotation)
                if concept_name not in phylogeny.keys():
                    # get the phylogeny from VARS kb
                    with requests.get(f'http://hurlstor.soest.hawaii.edu:8083/kb/v1/phylogeny/up/{concept_name}') \
                            as vars_tax_res:
                        if vars_tax_res.status_code == 200:
                            # this get us to phylum
                            try:
                                vars_tree = vars_tax_res.json()['children'][0]['children'][0]['children'][0]['children'][0]['children'][0]
                                phylogeny[concept_name] = {}
                            except KeyError:
                                print(f'\n{TERM_RED}VARS phylogeny for {annotation["concept"]} not in expected format{TERM_NORMAL}')
                                vars_tree = {}
                            while 'children' in vars_tree.keys():
                                if 'rank' in vars_tree.keys():  # sometimes it's not
                                    phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                                vars_tree = vars_tree['children'][0]
                            if 'rank' in vars_tree.keys():
                                phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                        else:
                            print(f'\n{TERM_RED}Unable to find record for {annotation["concept"]}{TERM_NORMAL}')

        formatted_images = []

        # add the records to a list, convert hyphens to underlines and remove excess data
        for record in image_records:
            concept_name = record['concept']

            # get image url
            image_url = record['image_references'][0]['url']
            for i in range(1, len(record['image_references'])):
                if '.png' in record['image_references'][i]['url']:
                    image_url = record['image_references'][i]['url']
                    break
            image_url = image_url.replace('http://hurlstor.soest.hawaii.edu/imagearchive',
                                          'https://hurlimage.soest.hawaii.edu')

            # get video reference url
            if 'recorded_timestamp' not in record.keys():
                break
            timestamp = parse_datetime(record['recorded_timestamp'])
            video_url = videos[0]
            for video in videos:
                if video[0] > timestamp:
                    break
                video_url = video
            time_diff = timestamp - video_url[0]
            video_url = f'{video_url[1]}#t={int(time_diff.total_seconds()) - 5}'

            annotation_dict = {
                'observation_uuid': record['observation_uuid'],
                'concept': concept_name,
                'identity_certainty': get_association(record, 'identity-certainty')['link_value'] if get_association(record, 'identity-certainty') else None,
                'identity_reference': get_association(record, 'identity-reference')['link_value'] if get_association(record, 'identity-reference') else None,
                'guide_photo': get_association(record, 'guide-photo')['to_concept'] if get_association(record, 'guide-photo') else None,
                'comment': get_association(record, 'comment')['link_value'] if get_association(record, 'comment') else None,
                'image_url': image_url,
                'video_url': video_url,
                'upon': get_association(record, 'upon')['to_concept'] if get_association(record, 'upon') else None,
                'recorded_timestamp': record['recorded_timestamp'],
                'video_sequence_name': video_sequence_name,
                'annotator': format_annotator(record['observer']),
                'depth': int(record['ancillary_data']['depth_meters']) if 'ancillary_data' in record.keys() and 'depth_meters' in record['ancillary_data'].keys() else None,
                'lat': round(record['ancillary_data']['latitude'], 3) if 'ancillary_data' in record.keys() and 'latitude' in record['ancillary_data'].keys() else None,
                'long': round(record['ancillary_data']['longitude'], 3) if 'ancillary_data' in record.keys() and 'longitude' in record['ancillary_data'].keys() else None,
                'temperature': round(record['ancillary_data']['temperature_celsius'], 2) if 'ancillary_data' in record.keys() and 'temperature_celsius' in record['ancillary_data'].keys() else None,
                'oxygen_ml_l': round(record['ancillary_data']['oxygen_ml_l'], 3) if 'ancillary_data' in record.keys() and 'oxygen_ml_l' in record['ancillary_data'].keys() else None,
            }

            if concept_name in phylogeny.keys():
                for key in phylogeny[concept_name].keys():
                    annotation_dict[key] = phylogeny[concept_name][key]
            formatted_images.append(annotation_dict)

        # add to dataframe for quick sorting
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
            'species'
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
            'recorded_timestamp'
        ])

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
                'video_sequence_name': row['video_sequence_name']
            })

        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(phylogeny, f, indent=2)
        except FileNotFoundError:
            os.makedirs('cache')
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(phylogeny, f, indent=2)

        print('processed!')
