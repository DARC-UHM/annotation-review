import re
from datetime import datetime
from typing import Dict


def parse_datetime(timestamp: str) -> datetime:
    """
    Returns a datetime object given a timestamp string.

    :param str timestamp: The timestamp to parse.
    :return datetime: The timestamp parsed as a datetime object.
    """
    if '.' in timestamp:
        return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')
    return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')


def get_association(annotation: Dict, link_name: str) -> dict:
    """
    Obtains an association value from the annotation data structure.

    :param Dict annotation: The complete annotation dictionary.
    :param str link_name: The specific key we want to get the value for.
    :return dict: The matching value dict.
    """
    for association in annotation['associations']:
        if association['link_name'] == link_name:
            return association
    return {}


def get_date_and_time(record: Dict) -> datetime:
    """
    Returns a datetime timestamp from a completed annotation record.

    :param Dict record: The annotation record after it has been converted from an AnnotationRow to a list.
    :return datetime: A datetime object of the observation date/time.
    """
    return datetime.strptime(record[OBSERVATION_DATE] + record[OBSERVATION_TIME], '%Y-%m-%d%H:%M:%S')


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
