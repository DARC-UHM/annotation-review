import pandas as pd
import requests

from .functions import *

TERM_RED = '\033[1;31;48m'
TERM_NORMAL = '\033[1;37;0m'


class CommentProcessor:
    """
    Fetches annotation information from the VARS db on HURLSTOR given a dict of comments (key = uuid). Merges the
    fetched annotation information with the data in the comment dict into an array of dicts (self.annotations).
    """
    def __init__(self, comments: Dict):
        self.comments = comments
        self.distilled_records = []
        self.load_comments()

    def load_comments(self):
        concept_phylogeny = {'Animalia': {}}

        formatted_comments = []

        # add formatted comments to list
        for comment in self.comments:
            annotation = requests.get(f'http://hurlstor.soest.hawaii.edu:8082/anno/v1/annotations/{comment}').json()
            concept_name = annotation['concept']

            if concept_name not in concept_phylogeny.keys():
                # get the phylogeny from VARS kb
                concept_phylogeny[concept_name] = {}
                with requests.get(f'http://hurlstor.soest.hawaii.edu:8083/kb/v1/phylogeny/up/{concept_name}') \
                        as vars_tax_res:
                    if vars_tax_res.status_code == 200:
                        # this get us to phylum
                        try:
                            vars_tree = vars_tax_res.json()['children'][0]['children'][0]['children'][0]['children'][0]['children'][0]
                        except KeyError:
                            print(f'\n{TERM_RED}VARS phylogeny for {annotation["concept"]} not in expected format{TERM_NORMAL}')
                            vars_tree = {}
                        while 'children' in vars_tree.keys():
                            if 'rank' in vars_tree.keys():  # sometimes it's not
                                concept_phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                            vars_tree = vars_tree['children'][0]
                        if 'rank' in vars_tree.keys():
                            concept_phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                    else:
                        print(f'\n{TERM_RED}Unable to find record for {annotation["concept"]}{TERM_NORMAL}')

            formatted_comments.append({
                'observation_uuid': annotation['observation_uuid'],
                'concept': concept_name,
                'identity-certainty': get_association(annotation, 'identity-certainty')['link_value'] if get_association(annotation, 'identity-certainty') else None,
                'identity-reference': get_association(annotation, 'identity-reference')['link_value'] if get_association(annotation, 'identity-reference') else None,
                'guide-photo': get_association(annotation, 'guide-photo')['to_concept'] if get_association(annotation, 'guide-photo') else None,
                'comment': get_association(annotation, 'comment')['link_value'] if get_association(annotation, 'comment') else None,
                'image_url': self.comments[comment]['image_url'],
                'video_url': self.comments[comment]['video_url'],
                'upon': get_association(annotation, 'upon')['to_concept'] if get_association(annotation, 'upon') else None,
                'recorded_timestamp': parse_datetime(annotation['recorded_timestamp']).strftime('%d %b %y %H:%M:%S UTC'),
                'video_sequence_name': self.comments[comment]['sequence'],
                'annotator': format_annotator(annotation['observer']),
                'depth': self.comments[comment]['depth'],
                'lat': self.comments[comment]['lat'] if 'lat' in self.comments[comment].keys() else None,
                'long': self.comments[comment]['long'] if 'long' in self.comments[comment].keys() else None,
                'temperature': self.comments[comment]['temperature'] if 'temperature' in self.comments[comment].keys() else None,
                'oxygen_ml_l': self.comments[comment]['oxygen_ml_l'] if 'oxygen_ml_l' in self.comments[comment].keys() else None,
                'phylum': concept_phylogeny[concept_name]['phylum'] if 'phylum' in concept_phylogeny[concept_name].keys() else None,
                'subphylum': concept_phylogeny[concept_name]['subphylum'] if 'subphylum' in concept_phylogeny[concept_name].keys() else None,
                'superclass': concept_phylogeny[concept_name]['superclass'] if 'superclass' in concept_phylogeny[concept_name].keys() else None,
                'class': concept_phylogeny[concept_name]['class'] if 'class' in concept_phylogeny[concept_name].keys() else None,
                'subclass': concept_phylogeny[concept_name]['subclass'] if 'subclass' in concept_phylogeny[concept_name].keys() else None,
                'superorder': concept_phylogeny[concept_name]['superorder'] if 'superorder' in concept_phylogeny[concept_name].keys() else None,
                'order': concept_phylogeny[concept_name]['order'] if 'order' in concept_phylogeny[concept_name].keys() else None,
                'suborder': concept_phylogeny[concept_name]['suborder'] if 'suborder' in concept_phylogeny[concept_name].keys() else None,
                'infraorder': concept_phylogeny[concept_name]['infraorder'] if 'infraorder' in concept_phylogeny[concept_name].keys() else None,
                'superfamily': concept_phylogeny[concept_name]['superfamily'] if 'superfamily' in concept_phylogeny[concept_name].keys() else None,
                'family': concept_phylogeny[concept_name]['family'] if 'family' in concept_phylogeny[concept_name].keys() else None,
                'subfamily': concept_phylogeny[concept_name]['subfamily'] if 'subfamily' in concept_phylogeny[concept_name].keys() else None,
                'genus': concept_phylogeny[concept_name]['genus'] if 'genus' in concept_phylogeny[concept_name].keys() else None,
                'species': concept_phylogeny[concept_name]['species'] if 'species' in concept_phylogeny[concept_name].keys() else None,
            })

        # add to dataframe for sorting
        annotation_df = pd.DataFrame(formatted_comments)
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
            'identity-reference',
            'identity-certainty',
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
                'identity_certainty': row['identity-certainty'],
                'identity_reference': row['identity-reference'],
                'guide_photo': row['guide-photo'],
                'comment': row['comment'],
                'image_url': row['image_url'],
                'video_url': row['video_url'],
                'upon': row['upon'],
                'recorded_timestamp': row['recorded_timestamp'],
                'video_sequence_name': row['video_sequence_name']
            })
