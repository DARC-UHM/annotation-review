import json
import os
import pandas as pd
import requests

from flask import session

from .functions import *

TERM_RED = '\033[1;31;48m'
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

        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'r') as f:
                phylogeny = json.load(f)
        except FileNotFoundError:
            phylogeny = {'Animalia': {}}

        # add formatted comments to list
        for comment in self.comments:
            print(self.comments[comment])
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

            comment_dict = {
                'observation_uuid': comment,
                'concept': concept_name,
                'scientific_name': self.comments[comment]['scientific_name'] if 'scientific_name' in self.comments[comment].keys() and self.comments[comment]['scientific_name'] else None,
                'all_localizations': json.loads(self.comments[comment]['all_localizations']) if 'all_localizations' in self.comments[comment].keys() and self.comments[comment]['all_localizations'] else None,
                'attracted': annotation['attributes']['Attracted'] if 'attributes' in annotation.keys() and 'Attracted' in annotation['attributes'].keys() else None,
                'categorical_abundance': annotation['attributes']['Categorical Abundance'] if 'attributes' in annotation.keys() and 'Categorical Abundance' in annotation['attributes'].keys() else None,
                'identification_remarks': annotation['attributes']['IdentificationRemarks'] if 'attributes' in annotation.keys() and 'IdentificationRemarks' in annotation['attributes'].keys() else None,
                'identified_by': annotation['attributes']['Identified By'] if 'attributes' in annotation.keys() and 'Identified By' in annotation['attributes'].keys() else None,
                'notes': annotation['attributes']['Notes'] if 'attributes' in annotation.keys() and 'Notes' in annotation['attributes'].keys() else None,
                'qualifier': annotation['attributes']['Qualifier'] if 'attributes' in annotation.keys() and 'Qualifier' in annotation['attributes'].keys() else None,
                'reason': annotation['attributes']['Reason'] if 'attributes' in annotation.keys() and 'Reason' in annotation['attributes'].keys() else None,
                'tentative_id': annotation['attributes']['Tentative ID'] if 'attributes' in annotation.keys() and 'Tentative ID' in annotation['attributes'].keys() else None,
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
                'lat': self.comments[comment]['lat'] if 'lat' in self.comments[comment].keys() else None,
                'long': self.comments[comment]['long'] if 'long' in self.comments[comment].keys() else None,
                'temperature': self.comments[comment]['temperature'] if 'temperature' in self.comments[comment].keys() else None,
                'oxygen_ml_l': self.comments[comment]['oxygen_ml_l'] if 'oxygen_ml_l' in self.comments[comment].keys() else None,
            }
            if concept_name in phylogeny.keys():
                comment_dict['phylum'] = phylogeny[concept_name]['phylum'] if 'phylum' in phylogeny[concept_name].keys() else None
                comment_dict['subphylum'] = phylogeny[concept_name]['subphylum'] if 'subphylum' in phylogeny[concept_name].keys() else None
                comment_dict['superclass'] = phylogeny[concept_name]['superclass'] if 'superclass' in phylogeny[concept_name].keys() else None
                comment_dict['class'] = phylogeny[concept_name]['class'] if 'class' in phylogeny[concept_name].keys() else None
                comment_dict['subclass'] = phylogeny[concept_name]['subclass'] if 'subclass' in phylogeny[concept_name].keys() else None
                comment_dict['superorder'] = phylogeny[concept_name]['superorder'] if 'superorder' in phylogeny[concept_name].keys() else None
                comment_dict['order'] = phylogeny[concept_name]['order'] if 'order' in phylogeny[concept_name].keys() else None
                comment_dict['suborder'] = phylogeny[concept_name]['suborder'] if 'suborder' in phylogeny[concept_name].keys() else None
                comment_dict['infraorder'] = phylogeny[concept_name]['infraorder'] if 'infraorder' in phylogeny[concept_name].keys() else None
                comment_dict['superfamily'] = phylogeny[concept_name]['superfamily'] if 'superfamily' in phylogeny[concept_name].keys() else None
                comment_dict['family'] = phylogeny[concept_name]['family'] if 'family' in phylogeny[concept_name].keys() else None
                comment_dict['subfamily'] = phylogeny[concept_name]['subfamily'] if 'subfamily' in phylogeny[concept_name].keys() else None
                comment_dict['genus'] = phylogeny[concept_name]['genus'] if 'genus' in phylogeny[concept_name].keys() else None
                comment_dict['species'] = phylogeny[concept_name]['species'] if 'species' in phylogeny[concept_name].keys() else None
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
