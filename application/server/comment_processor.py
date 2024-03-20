import json
import os
import pandas as pd
import requests

from flask import session

from .functions import *

TERM_RED = '\033[1;31;48m'
TERM_YELLOW = '\033[1;93m'
TERM_NORMAL = '\033[1;37;0m'


class CommentProcessor:
    """
    Fetches annotation information from the VARS db on HURLSTOR and Tator given a dict of comments (key = uuid). Merges
    fetched annotations with the data in the comment dict into an array of dicts (self.annotations).
    """
    def __init__(self, comments: Dict):
        self.comments = comments
        self.distilled_records = []
        self.load_comments()

    def load_comments(self):
        formatted_comments = []
        no_match_records = set()

        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'r') as f:
                phylogeny = json.load(f)
        except FileNotFoundError:
            phylogeny = {'Animalia': {}}

        # add formatted comments to list
        for comment in self.comments:
            if 'scientific_name' not in self.comments[comment].keys()\
                    or self.comments[comment]['scientific_name'] is None\
                    or self.comments[comment]['scientific_name'] == '':  # vars annotation
                annotation = requests.get(f'{os.environ.get("ANNOSAURUS_URL")}/annotations/{comment}').json()
                concept_name = annotation['concept']
            else:  # tator localization
                concept_name = self.comments[comment]['scientific_name']
                annotation = requests.get(
                    f'https://cloud.tator.io/rest/Localization/{comment}',
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Token {session["tator_token"]}',
                    }
                )
                annotation = annotation.json()
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
                        print(f'\n{TERM_RED}Unable to find record for {annotation["concept"]}{TERM_NORMAL}')

            comment_dict = {
                'observation_uuid': comment,
                'concept': concept_name,
                'scientific_name': self.comments[comment].get('scientific_name'),
                'all_localizations': json.loads(self.comments[comment].get('all_localizations')) if self.comments[comment].get('all_localizations') else None,
                'attracted': annotation['attributes'].get('Attracted') if annotation.get('attributes') else None,
                'categorical_abundance': annotation['attributes'].get('Categorical Abundance') if annotation.get('attributes') else None,
                'identification_remarks': annotation['attributes'].get('IdentificationRemarks') if annotation.get('attributes') else None,
                'identified_by': annotation['attributes'].get('Identified By') if annotation.get('attributes') else None,
                'notes': annotation['attributes'].get('Notes') if annotation.get('attributes') else None,
                'qualifier': annotation['attributes'].get('Qualifier') if annotation.get('attributes') else None,
                'reason': annotation['attributes'].get('Reason') if annotation.get('attributes') else None,
                'tentative_id': annotation['attributes'].get('Tentative ID') if annotation.get('attributes') else None,
                'identity_certainty': get_association(annotation, 'identity-certainty')['link_value'] if get_association(annotation, 'identity-certainty') else None,
                'identity_reference': get_association(annotation, 'identity-reference')['link_value'] if get_association(annotation, 'identity-reference') else None,
                'guide-photo': get_association(annotation, 'guide-photo')['to_concept'] if get_association(annotation, 'guide-photo') else None,
                'comment': get_association(annotation, 'comment')['link_value'] if get_association(annotation, 'comment') else None,
                'image_url': self.comments[comment]['image_url'],
                'video_url': self.comments[comment]['video_url'],
                'upon': get_association(annotation, 'upon')['to_concept'] if get_association(annotation, 'upon') else None,
                'recorded_timestamp': parse_datetime(annotation['recorded_timestamp']).strftime('%d %b %y %H:%M:%S UTC') if 'recorded_timestamp' in annotation.keys() else None,
                'video_sequence_name': self.comments[comment]['sequence'],
                'annotator': format_annotator(annotation['observer']) if 'observer' in annotation.keys() else self.comments[comment]['annotator'],
                'depth': self.comments[comment]['depth'],
                'lat': self.comments[comment].get('lat'),
                'long': self.comments[comment].get('long'),
                'temperature': self.comments[comment].get('temperature'),
                'oxygen_ml_l': self.comments[comment].get('oxygen_ml_l'),
            }
            if concept_name in phylogeny.keys():
                for key in phylogeny[concept_name].keys():
                    comment_dict[key] = phylogeny[concept_name][key]
            formatted_comments.append(comment_dict)

        # add to dataframe for sorting
        annotation_df = pd.DataFrame(formatted_comments, columns=[
            'observation_uuid',
            'concept',
            'scientific_name',
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
                'scientific_name': row['scientific_name'],
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
                'comment': row['comment'],
                'image_url': row['image_url'],
                'video_url': row['video_url'],
                'upon': row['upon'],
                'recorded_timestamp': row['recorded_timestamp'],
                'video_sequence_name': row['video_sequence_name']
            })

        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(phylogeny, f, indent=2)
        except FileNotFoundError:
            os.makedirs('cache')
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(phylogeny, f, indent=2)
