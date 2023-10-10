from datetime import datetime
import re


def parse_datetime(timestamp: str) -> datetime:
    """
    Returns a datetime object given a timestamp string.

    :param str timestamp: The timestamp to parse.
    :return datetime: The timestamp parsed as a datetime object.
    """
    if '.' in timestamp:
        return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
    return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')


def get_association(annotation, link_name):
    """ Obtains an association value from the annotation data structure """
    for association in annotation['associations']:
        if association['link_name'] == link_name:
            return association
    return None


def format_annotator(annotator):
    """ Format VARS annotator name. Most are formatted as "FirstnameLastname", with some exceptions """
    if annotator == 'hcarlson':
        return 'Harold Carlson'
    else:
        return re.sub('([a-zA-Z]+)([A-Z])', r'\1 \2', annotator)
