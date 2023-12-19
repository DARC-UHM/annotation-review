import requests

from typing import Dict

from .functions import *

TERM_RED = '\033[1;31;48m'
TERM_NORMAL = '\033[1;37;0m'


class CommentProcessor:
    """
    Fetches annotation information from the VARS db on HURLSTOR given a dict of comments (key = uuid). Merges the
    fetched annotation information with the data in the comment dict into an array of dicts (self.annotations).
    """
    def __init__(self, comments: Dict):
        self.annotations = []
        self.comments = comments
        self.load_comments()

    def load_comments(self):
        concept_phylogeny = {'Animalia': {}}
        for comment in self.comments:
            joined_annotation = {}  # joined comment data and annotation data from VARS
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

            joined_annotation['phylum'] = concept_phylogeny[concept_name]['phylum'] if 'phylum' in concept_phylogeny[concept_name].keys() else None
            joined_annotation['subphylum'] = concept_phylogeny[concept_name]['subphylum'] if 'subphylum' in concept_phylogeny[concept_name].keys() else None
            joined_annotation['superclass'] = concept_phylogeny[concept_name]['superclass'] if 'superclass' in concept_phylogeny[concept_name].keys() else None
            joined_annotation['class'] = concept_phylogeny[concept_name]['class'] if 'class' in concept_phylogeny[concept_name].keys() else None
            joined_annotation['subclass'] = concept_phylogeny[concept_name]['subclass'] if 'subclass' in concept_phylogeny[concept_name].keys() else None
            joined_annotation['superorder'] = concept_phylogeny[concept_name]['superorder'] if 'superorder' in concept_phylogeny[concept_name].keys() else None
            joined_annotation['order'] = concept_phylogeny[concept_name]['order'] if 'order' in concept_phylogeny[concept_name].keys() else None
            joined_annotation['suborder'] = concept_phylogeny[concept_name]['suborder'] if 'suborder' in concept_phylogeny[concept_name].keys() else None
            joined_annotation['infraorder'] = concept_phylogeny[concept_name]['infraorder'] if 'infraorder' in concept_phylogeny[concept_name].keys() else None
            joined_annotation['superfamily'] = concept_phylogeny[concept_name]['superfamily'] if 'superfamily' in concept_phylogeny[concept_name].keys() else None
            joined_annotation['family'] = concept_phylogeny[concept_name]['family'] if 'family' in concept_phylogeny[concept_name].keys() else None
            joined_annotation['subfamily'] = concept_phylogeny[concept_name]['subfamily'] if 'subfamily' in concept_phylogeny[concept_name].keys() else None
            joined_annotation['genus'] = concept_phylogeny[concept_name]['genus'] if 'genus' in concept_phylogeny[concept_name].keys() else None
            joined_annotation['species'] = concept_phylogeny[concept_name]['species'] if 'species' in concept_phylogeny[concept_name].keys() else None
            joined_annotation['observation_uuid'] = annotation['observation_uuid']
            joined_annotation['concept'] = concept_name
            joined_annotation['depth'] = self.comments[comment]['depth']
            joined_annotation['annotator'] = format_annotator(annotation['observer'])
            joined_annotation['recorded_timestamp'] = parse_datetime(annotation['recorded_timestamp']).strftime('%d %b %y %H:%M:%S UTC')
            joined_annotation['video_url'] = self.comments[comment]['video_url']
            joined_annotation['image_url'] = self.comments[comment]['image_url']
            joined_annotation['video_sequence_name'] = self.comments[comment]['sequence']
            if get_association(annotation, 'identity-certainty'):
                joined_annotation['identity_certainty'] = get_association(annotation, 'identity-certainty')['link_value']
            if get_association(annotation, 'identity-reference'):
                joined_annotation['identity_reference'] = get_association(annotation, 'identity-reference')['link_value']
            if get_association(annotation, 'upon'):
                joined_annotation['upon'] = get_association(annotation, 'upon')['to_concept']
            if get_association(annotation, 'comment'):
                joined_annotation['comment'] = get_association(annotation, 'comment')['link_value']
            if get_association(annotation, 'guide-photo'):
                joined_annotation['guide_photo'] = get_association(annotation, 'guide-photo')['to_concept']

            self.annotations.append(joined_annotation)
