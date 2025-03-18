import re
from datetime import datetime, timedelta
from typing import Dict, Optional


def parse_datetime(timestamp: str) -> datetime:
    """
    Returns a datetime object given a timestamp string.

    :param str timestamp: The timestamp to parse.
    :return datetime: The timestamp parsed as a datetime object.
    """
    if '.' in timestamp:
        return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
    return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')


def extract_recorded_datetime(json_object: Dict) -> Optional[datetime]:
    """
    Returns a datetime object of the recorded timestamp given a JSON annotation record.

    :param Dict json_object: An annotation record.
    :return datetime: A datetime object of the timestamp from the json object.
    """
    if not json_object:
        return None
    if '.' in json_object['recorded_timestamp']:
        timestamp = datetime.strptime(json_object['recorded_timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
        if timestamp.microsecond >= 500000:
            return timestamp.replace(microsecond=0) + timedelta(seconds=1)
        return timestamp.replace(microsecond=0)
    return datetime.strptime(json_object['recorded_timestamp'], '%Y-%m-%dT%H:%M:%SZ')


def get_association(annotation: Dict, link_name: str) -> dict:
    """
    Obtains an association value from the annotation data structure.

    :param Dict annotation: The complete annotation dictionary.
    :param str link_name: The specific key we want to get the value for.
    :return dict: The matching value dict.
    """
    if 'associations' not in annotation.keys():
        return {}
    for association in annotation['associations']:
        if association['link_name'] == link_name:
            return association
    return {}


def format_annotator(annotator: str) -> str:
    """
    Format VARS annotator name. Most are formatted as "FirstnameLastname", with some exceptions.

    :param str annotator: VARS username to format
    :return str: Formatted name
    """
    if annotator == 'hcarlson':
        return 'Harold Carlson'
    else:
        return re.sub('([a-zA-Z]+)([A-Z])', r'\1 \2', annotator)


def flatten_taxa_tree(tree: Dict, flat: Dict):
    """
    Recursive function taking a taxonomy tree returned from WoRMS API and flattening it into a single dictionary.

    :param Dict tree: The nested taxon tree from WoRMS.
    :param Dict flat: The newly created flat taxon tree.
    """
    flat[tree['rank'].lower()] = tree['scientificname']
    if tree['child'] is not None:
        flatten_taxa_tree(tree['child'], flat)
    return flat
