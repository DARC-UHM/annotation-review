import json
import os
import pandas as pd
import numpy as np
import requests
import sys

from flask import session
from json import JSONDecodeError

from application.util.functions import *
from application.util.constants import TERM_RED, TERM_YELLOW, TERM_NORMAL


class CommentProcessor:
    """
    Fetches annotation information from the VARS db on HURLSTOR and Tator given a dict of comments (key = uuid). Merges
    fetched annotations with the data in the comment dict into an array of dicts (self.annotations).
    """
    def __init__(self, comments: Dict, annosaurus_url: str, vars_phylogeny_url: str, tator_localizations_url: str):
        self.comments = comments
        self.annosaurus_url = annosaurus_url
        self.vars_phylogeny_url = vars_phylogeny_url
        self.tator_localizations_url = tator_localizations_url
        self.distilled_records = []
        self.missing_records = []
        self.no_match_records = set()
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
        if session.get('tator_token'):
            for comment in self.comments:
                if 'all_localizations' in self.comments[comment].keys() and self.comments[comment]['all_localizations'] is not None:
                    # get the media id from the video url (not stored as its own field)
                    media_id = self.comments[comment]['video_url'].split('/')[-1].split('&')[0]
                    media_ids.add(media_id)
            for i in range(0, len(media_ids), 300):  # just get all localizations for each media id
                chunk = list(media_ids)[i:i + 300]
                # fixme (?) vvvv potential bug using hardcoded "26" as project id (but probably fine) vvvv
                get_localization_res = requests.get(
                    url=f'{self.tator_localizations_url}/26?media_id={",".join(map(str, chunk))}',
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Token {session["tator_token"]}',
                    })
                localizations += get_localization_res.json()

        # add formatted comments to list
        for comment in self.comments:
            concept_name = None
            comment_dict = {
                'observation_uuid': comment,
                'image_url': self.comments[comment].get('image_url'),
                'video_url': self.comments[comment].get('video_url'),
                'video_sequence_name': self.comments[comment]['sequence'],
            }

            if 'all_localizations' not in self.comments[comment].keys()\
                    or self.comments[comment]['all_localizations'] is None\
                    or self.comments[comment]['all_localizations'] == '':
                # vars annotation
                guide_photo = None
                upon = None
                identity_certainty = None
                identity_reference = None
                depth = None
                vars_comment = None
                vars_res = requests.get(url=f'{self.annosaurus_url}/annotations/{comment}')
                try:
                    annotation = vars_res.json()
                    concept_name = annotation['concept']
                except (JSONDecodeError, KeyError):
                    problem_comment = self.comments[comment]
                    print(f'{TERM_RED}ERROR: Could not find annotation with UUID {comment} in VARS ({problem_comment["sequence"]}, {problem_comment["timestamp"]}){TERM_NORMAL}')
                    self.missing_records.append(problem_comment)
                    continue
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
                if annotation.get('ancillary_data'):
                    # get ctd
                    for ancillary_data in annotation['ancillary_data']:
                        if ancillary_data == 'depth_meters':
                            depth = annotation['ancillary_data']['depth_meters']
                comment_dict['concept'] = concept_name
                comment_dict['recorded_timestamp'] = parse_datetime(annotation['recorded_timestamp']).strftime('%d %b %y %H:%M:%S UTC') if 'recorded_timestamp' in annotation.keys() else None
                comment_dict['annotator'] = format_annotator(annotation['observer']) if 'observer' in annotation.keys() else self.comments[comment]['annotator']
                comment_dict['associations'] = annotation.get('associations')
                comment_dict['identity_reference'] = identity_reference
                comment_dict['guide-photo'] = guide_photo
                comment_dict['upon'] = upon
                comment_dict['identity_certainty'] = identity_certainty
                comment_dict['depth'] = round(depth) if depth else None
                comment_dict['comment'] = vars_comment
            else:
                # tator annotation
                if session.get('tator_token'):
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
                        comment_dict['good_image'] = True
                    else:
                        comment_dict['good_image'] = False
                    concept_name = annotation['attributes']['Scientific Name']
                    comment_dict['all_localizations'] = json.loads(self.comments[comment].get('all_localizations'))
                    comment_dict['scientific_name'] = annotation['attributes']['Scientific Name']
                    comment_dict['media_id'] = annotation['media']
                    comment_dict['frame'] = annotation['frame']
                    comment_dict['recorded_timestamp'] = parse_datetime(annotation['recorded_timestamp']).strftime('%d %b %y %H:%M:%S UTC') if 'recorded_timestamp' in annotation.keys() else None
                    comment_dict['annotator'] = format_annotator(annotation['observer']) if 'observer' in annotation.keys() else self.comments[comment]['annotator']
                    if annotation.get('attributes'):
                        comment_dict['attracted'] = annotation['attributes'].get('Attracted')
                        comment_dict['frame_url'] = f'/tator/frame/{annotation["media"]}/{annotation["frame"]}'
                        comment_dict['categorical_abundance'] = annotation['attributes'].get('Categorical Abundance')
                        comment_dict['identification_remarks'] = annotation['attributes'].get('IdentificationRemarks')
                        comment_dict['morphospecies'] = annotation['attributes'].get('Morphospecies')
                        comment_dict['identified_by'] = annotation['attributes'].get('Identified By')
                        comment_dict['notes'] = annotation['attributes'].get('Notes')
                        comment_dict['qualifier'] = annotation['attributes'].get('Qualifier')
                        comment_dict['reason'] = annotation['attributes'].get('Reason')
                        comment_dict['tentative_id'] = annotation['attributes'].get('Tentative ID')
                else:
                    annotation = {}
                    comment_dict['all_localizations'] = [{}]
            if concept_name and concept_name not in phylogeny.keys() and concept_name not in self.no_match_records:
                # get the phylogeny from VARS kb
                with requests.get(url=f'{self.vars_phylogeny_url}/{concept_name}') \
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
                        self.no_match_records.add(concept_name)
                        print(f'\n{TERM_RED}Unable to find record for {concept_name}{TERM_NORMAL}')
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
            'morphospecies',
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
        annotation_df = annotation_df.replace({pd.NA: None, np.nan: None})
        temp_record_list = annotation_df.to_dict(orient='records')
        for record in temp_record_list:
            anno_dict = {}
            for key, value in record.items():
                if value is not None:
                    anno_dict[key] = value
            self.distilled_records.append(anno_dict)
        print('processed!')

        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(phylogeny, f, indent=2)
        except FileNotFoundError:
            os.makedirs('cache')
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(phylogeny, f, indent=2)
