from typing import Dict

import requests


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
            joined_annotation['recorded_timestamp'] = annotation['recorded_timestamp']
            joined_annotation['video_url'] = self.comments[comment]['video_url']
            joined_annotation['image_url'] = self.comments[comment]['image_url']
            joined_annotation['video_sequence_name'] = self.comments[comment]['sequence']

            temp = get_association(annotation, 'identity_certainty')
            if temp:
                joined_annotation['identity_certainty'] = temp['link_value']

            temp = get_association(annotation, 'identity_reference')
            if temp:
                joined_annotation['identity_reference'] = temp['link_value']

            temp = get_association(annotation, 'upon')
            if temp:
                joined_annotation['upon'] = temp['to_concept']

            temp = get_association(annotation, 'comment')
            if temp:
                joined_annotation['comment'] = temp['link_value']

            temp = get_association(annotation, 'guide_photo')
            if temp:
                joined_annotation['guide_photo'] = temp['to_concept']

            self.annotations.append(joined_annotation)
