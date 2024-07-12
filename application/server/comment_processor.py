import json
import os
import pandas as pd
import requests
import sys

from flask import session
from json import JSONDecodeError

from .functions import *
from .constants import TERM_RED, TERM_YELLOW, TERM_NORMAL


class CommentProcessor:
    """
    Fetches annotation information from the VARS db on HURLSTOR and Tator given a dict of comments (key = uuid). Merges
    fetched annotations with the data in the comment dict into an array of dicts (self.annotations).
    """
    def __init__(self, comments: Dict):
        self.comments = comments
        self.distilled_records = []
        self.missing_records = []
        self.load_comments()

    def load_comments(self):
        formatted_comments = []
        no_match_records = set()

        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'r') as f:
                phylogeny = json.load(f)
        except FileNotFoundError:
            phylogeny = {'Animalia': {}}

        print(f'Processing {len(self.comments)} comments...', end='')
        sys.stdout.flush()

        # get all the tator localizations first, because each tator call takes forever
        media_ids = set()
        localizations = []
        for comment in self.comments:
            if 'all_localizations' in self.comments[comment].keys() and self.comments[comment]['all_localizations'] is not None:
                # get the media id from the video url (not stored as its own field)
                media_id = self.comments[comment]['video_url'].split('/')[-1].split('&')[0]
                media_ids.add(media_id)
        for i in range(0, len(media_ids), 300):  # just get all localizations for each media id
            chunk = list(media_ids)[i:i + 300]
            # fixme (?) vvvv potential bug using hardcoded "26" as project id (but probably fine) vvvv
            get_localization_res = requests.get(
                url=f'https://cloud.tator.io/rest/Localizations/26?media_id={",".join(map(str, chunk))}',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Token {session["tator_token"]}',
                })
            localizations += get_localization_res.json()

        # add formatted comments to list
        for comment in self.comments:
            identity_certainty = None
            identity_reference = None
            guide_photo = None
            vars_comment = None
            upon = None
            good_image = False
            media_id = None
            frame = None

            if 'all_localizations' not in self.comments[comment].keys()\
                    or self.comments[comment]['all_localizations'] is None\
                    or self.comments[comment]['all_localizations'] == '':
                # vars annotation
                try:
                    annotation = requests.get(url=f'{os.environ.get("ANNOSAURUS_URL")}/annotations/{comment}').json()
                except JSONDecodeError:
                    problem_comment = self.comments[comment]
                    print(f'{TERM_RED}ERROR: Could not find annotation with UUID {comment} in VARS ({problem_comment["sequence"]}, {problem_comment["timestamp"]}){TERM_NORMAL}')
                    self.missing_records.append(problem_comment)
                    continue
                concept_name = annotation['concept']
                if annotation.get('associations'):
                    for association in annotation['associations']:
                        if association['link_name'] == 'identity-certainty':
                            identity_certainty = association['link_value']
                        elif association['link_name'] == 'identity-reference':
                            identity_reference = association['link_value']
                        elif association['link_name'] == 'guide-photo':
                            guide_photo = association['to_concept']
                        elif association['link_name'] == 'upon':
                            upon = association['to_concept']
                        elif association['link_name'] == 'comment':
                            vars_comment = association['link_value']
            else:
                # tator localization
                annotation = next((loco for loco in localizations if loco['elemental_id'] == comment), None)
                if annotation is None:
                    problem_comment = self.comments[comment]
                    problem_comment['timestamp'] = f'No timestamp available'
                    print(f'{TERM_RED}ERROR: Could not find annotation with UUID {comment} in Tator ({problem_comment["sequence"]}, {problem_comment["timestamp"]}){TERM_NORMAL}')
                    self.missing_records.append(problem_comment)
                    continue
                elif annotation['variant_deleted']:
                    problem_comment = self.comments[comment]
                    problem_comment['timestamp'] = f'Media ID: {annotation["media"]}, Frame: {annotation["frame"]}'
                    print(f'{TERM_RED}ERROR: Could not find annotation with UUID {comment} in Tator ({problem_comment["sequence"]}, {problem_comment["timestamp"]}){TERM_NORMAL}')
                    self.missing_records.append(problem_comment)
                    continue
                if annotation['attributes'].get('Good Image'):
                    good_image = True
                concept_name = annotation['attributes']['Scientific Name']
                media_id = annotation['media']
                frame = annotation['frame']
            if concept_name not in phylogeny.keys():
                # get the phylogeny from VARS kb
                with requests.get(url=f'http://hurlstor.soest.hawaii.edu:8083/v1/phylogeny/up/{concept_name}') \
                        as vars_tax_res:
                    if vars_tax_res.status_code == 200:
                        # this get us to phylum
                        try:
                            vars_tree = vars_tax_res.json()['children'][0]['children'][0]['children'][0]['children'][0]['children'][0]
                            phylogeny[concept_name] = {}
                        except KeyError:
                            if concept_name not in no_match_records:
                                no_match_records.add(concept_name)
                                print(f'{TERM_YELLOW}WARNING: Could not find phylogeny for concept "{annotation["concept"]}" in VARS knowledge base{TERM_NORMAL}')
                            vars_tree = {}
                        while 'children' in vars_tree.keys():
                            if 'rank' in vars_tree.keys():  # sometimes it's not
                                phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                            vars_tree = vars_tree['children'][0]
                        if 'rank' in vars_tree.keys():
                            phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                    else:
                        print(f'\n{TERM_RED}Unable to find record for {concept_name}{TERM_NORMAL}')

            comment_dict = {
                'observation_uuid': comment,
                'concept': concept_name,
                'scientific_name': concept_name if 'all_localizations' in self.comments[comment].keys() else None,
                'associations': annotation.get('associations'),
                'all_localizations': json.loads(self.comments[comment].get('all_localizations')) if self.comments[comment].get('all_localizations') else None,
                'attracted': annotation['attributes'].get('Attracted') if annotation.get('attributes') else None,
                'categorical_abundance': annotation['attributes'].get('Categorical Abundance') if annotation.get('attributes') else None,
                'identification_remarks': annotation['attributes'].get('IdentificationRemarks') if annotation.get('attributes') else None,
                'identified_by': annotation['attributes'].get('Identified By') if annotation.get('attributes') else None,
                'notes': annotation['attributes'].get('Notes') if annotation.get('attributes') else None,
                'qualifier': annotation['attributes'].get('Qualifier') if annotation.get('attributes') else None,
                'reason': annotation['attributes'].get('Reason') if annotation.get('attributes') else None,
                'tentative_id': annotation['attributes'].get('Tentative ID') if annotation.get('attributes') else None,
                'identity_certainty': identity_certainty,
                'identity_reference': identity_reference,
                'guide-photo': guide_photo,
                'good_image': good_image,
                'media_id': media_id,
                'frame': frame,
                'comment': vars_comment,
                'image_url': self.comments[comment]['image_url'],
                'frame_url': f'/tator/frame/{media_id}/{frame}',
                'video_url': self.comments[comment].get('video_url'),
                'upon': upon,
                'recorded_timestamp': parse_datetime(annotation['recorded_timestamp']).strftime('%d %b %y %H:%M:%S UTC') if 'recorded_timestamp' in annotation.keys() else None,
                'video_sequence_name': self.comments[comment]['sequence'],
                'annotator': format_annotator(annotation['observer']) if 'observer' in annotation.keys() else self.comments[comment]['annotator'],
                'depth': self.comments[comment].get('depth'),
                'lat': self.comments[comment].get('lat'),
                'long': self.comments[comment].get('long'),
                'temperature': self.comments[comment].get('temperature'),
                'oxygen_ml_l': self.comments[comment].get('oxygen_ml_l'),
            }
            if concept_name in phylogeny.keys():
                for key in phylogeny[concept_name].keys():
                    # split to account for worms 'Phylum (Division)' case
                    comment_dict[key.split(' ')[0]] = phylogeny[concept_name][key]
            formatted_comments.append(comment_dict)

        # add to dataframe for sorting
        annotation_df = pd.DataFrame(formatted_comments, columns=[
            'observation_uuid',
            'concept',
            'scientific_name',
            'associations',
            'all_localizations',
            'attracted',
            'categorical_abundance',
            'identification_remarks',
            'identified_by',
            'notes',
            'qualifier',
            'reason',
            'tentative_id',
            'identity_certainty',
            'identity_reference',
            'guide_photo',
            'good_image',
            'media_id',
            'frame',
            'comment',
            'image_url',
            'frame_url',
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
                'scientific_name': row['scientific_name'],
                'associations': row['associations'],
                'all_localizations': row['all_localizations'],
                'attracted': row['attracted'],
                'categorical_abundance': row['categorical_abundance'],
                'identification_remarks': row['identification_remarks'],
                'identified_by': row['identified_by'],
                'notes': row['notes'],
                'qualifier': row['qualifier'],
                'reason': row['reason'],
                'tentative_id': row['tentative_id'],
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
                'good_image': row['good_image'],
                'media_id': row['media_id'],
                'frame': row['frame'],
                'comment': row['comment'],
                'image_url': row['image_url'],
                'frame_url': row['frame_url'],
                'video_url': row['video_url'],
                'upon': row['upon'],
                'recorded_timestamp': row['recorded_timestamp'],
                'video_sequence_name': row['video_sequence_name']
            })

        print('processed!')

        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(phylogeny, f, indent=2)
        except FileNotFoundError:
            os.makedirs('cache')
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(phylogeny, f, indent=2)
