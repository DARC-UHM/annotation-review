import requests

from typing import Dict

from .functions import *


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
        for comment in self.comments:
            joined_annotation = {}
            annotation = requests.get(f'http://hurlstor.soest.hawaii.edu:8082/anno/v1/annotations/{comment}').json()

            with requests.get(f'http://hurlstor.soest.hawaii.edu:8083/kb/v1/phylogeny/up/{annotation["concept"]}') \
                    as vars_tax_res:
                if vars_tax_res.status_code == 200:
                    joined_annotation['phylum'] = \
                        vars_tax_res.json()['children'][0]['children'][0]['children'][0]['children'][0]['children'][0]['name']

            joined_annotation['observation_uuid'] = annotation['observation_uuid']
            joined_annotation['concept'] = annotation['concept']
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