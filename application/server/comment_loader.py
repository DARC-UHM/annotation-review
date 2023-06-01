import re
import requests

from typing import Dict

from application.server.image_loader import parse_datetime


def get_association(annotation, link_name):
    """ Obtains an association value from the annotation data structure """
    for association in annotation['associations']:
        if association['link_name'] == link_name:
            return association
    return None


class CommentLoader:
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
            joined_annotation['annotator'] = re.sub('([a-zA-Z]+)([A-Z])', r'\1 \2', annotation['observer'])
            joined_annotation['recorded_timestamp'] = parse_datetime(annotation['recorded_timestamp']).strftime('%d %b %y %H:%M:%S UTC')
            joined_annotation['video_url'] = self.comments[comment]['video_url']
            joined_annotation['image_url'] = self.comments[comment]['image_url']
            joined_annotation['video_sequence_name'] = self.comments[comment]['sequence']
            if get_association(annotation, 'identity_certainty'):
                joined_annotation['identity_certainty'] = get_association(annotation, 'identity_certainty')['link_value']
            if get_association(annotation, 'identity_reference'):
                joined_annotation['identity_reference'] = get_association(annotation, 'identity_reference')['link_value']
            if get_association(annotation, 'upon'):
                joined_annotation['upon'] = get_association(annotation, 'upon')['to_concept']
            if get_association(annotation, 'comment'):
                joined_annotation['comment'] = get_association(annotation, 'comment')['link_value']
            if get_association(annotation, 'guide_photo'):
                joined_annotation['guide_photo'] = get_association(annotation, 'guide_photo')['to_concept']

            self.annotations.append(joined_annotation)
