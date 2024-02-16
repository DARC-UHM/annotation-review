import json
import os
import sys

import requests
import pandas as pd
import tator
from flask import session

from .constants import KNOWN_ANNOTATORS
from .functions import *

TERM_RED = '\033[1;31;48m'
TERM_NORMAL = '\033[1;37;0m'


class TatorQaqcProcessor:
    """
    Fetches annotation information from the Tator given a project id, section id, and list of deployments.
    Filters and formats the annotations for the various QA/QC checks.
    """

    def __init__(self, project_id: int, section_id: int, api: tator.api, deployment_list: list):
        self.project_id = project_id
        self.section_id = section_id
        self.api = api
        self.deployments = deployment_list
        print(session['tator_token'])
        self.localizations = self.fetch_localizations()

    def fetch_localizations(self):
        print('Fetching localizations...', end='')
        sys.stdout.flush()
        media_ids = []
        localizations = []
        for deployment in self.deployments:
            media_ids += session[f'{self.project_id}_{self.section_id}'][deployment]
        # REST is much faster than Python API for large queries
        # adding too many media ids results in a query that is too long, so we have to break it up
        for i in range(0, len(media_ids), 300):
            chunk = media_ids[i:i + 300]
            req = requests.get(
                f'https://cloud.tator.io/rest/Localizations/{self.project_id}?media_id={",".join(map(str, chunk))}',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Token {session["tator_token"]}',
                })
            localizations += req.json()
        print('fetched!')
        return localizations

    def process_records(self):
        if not self.localizations:
            return

        print('Processing localizations...', end='')
        sys.stdout.flush()

        formatted_localizations = []
        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'r') as f:
                phylogeny = json.load(f)
        except FileNotFoundError:
            phylogeny = {}

        for localization in localizations:
            if localization['type'] not in [48, 49]:
                print('Mystery localization skipped')
                continue
            scientific_name = localization['attributes']['Scientific Name']
            if scientific_name not in phylogeny.keys():
                req = requests.get(
                    f'https://www.marinespecies.org/rest/AphiaIDByName/{scientific_name}?marine_only=true')
                phylogeny[scientific_name] = {}
                if req.status_code == 200 and req.json() != -999:  # -999 means more than one matching record
                    aphia_id = req.json()
                    req = requests.get(f'https://www.marinespecies.org/rest/AphiaClassificationByAphiaID/{aphia_id}')
                    if req.status_code == 200:
                        phylogeny[scientific_name] = flatten_taxa_tree(req.json(), {})
                else:
                    req = requests.get(
                        f'https://www.marinespecies.org/rest/AphiaRecordsByName/{scientific_name}?like=false&marine_only=true&offset=1')
                    if req.status_code == 200 and len(req.json()) > 0:
                        # just take the first accepted record
                        for record in req.json():
                            if record['status'] == 'accepted':
                                req = requests.get(
                                    f'https://www.marinespecies.org/rest/AphiaClassificationByAphiaID/{record["AphiaID"]}')
                                if req.status_code == 200:
                                    phylogeny[scientific_name] = flatten_taxa_tree(req.json(), {})
                                break
            formatted_localizations.append({
                'id': localization['id'],
                'all_localizations': {
                    'id': localization['id'],
                    'type': localization['type'],
                    'points': [round(localization['x'], 5), round(localization['y'], 5)],
                    'dimensions': [localization['width'], localization['height']] if localization[
                                                                                         'type'] == 48 else None,
                },
                'video_sequence_name': deployment_media_dict[localization['media']],
                'scientific_name': scientific_name,
                'count': 0 if localization['type'] == 48 else 1,
                'attracted': localization['attributes']['Attracted'] if 'Attracted' in localization[
                    'attributes'].keys() else None,
                'categorical_abundance': localization['attributes'][
                    'Categorical Abundance'] if 'Categorical Abundance' in localization['attributes'].keys() else None,
                'identification_remarks': localization['attributes'][
                    'IdentificationRemarks'] if 'IdentificationRemarks' in localization['attributes'].keys() else None,
                'identified_by': localization['attributes']['Identified By'] if 'Identified By' in localization[
                    'attributes'].keys() else None,
                'notes': localization['attributes']['Notes'] if 'Notes' in localization['attributes'].keys() else None,
                'qualifier': localization['attributes']['Qualifier'] if 'Qualifier' in localization[
                    'attributes'].keys() else None,
                'reason': localization['attributes']['Reason'] if 'Reason' in localization[
                    'attributes'].keys() else None,
                'tentative_id': localization['attributes']['Tentative ID'] if 'Tentative ID' in localization[
                    'attributes'].keys() else None,
                'annotator': KNOWN_ANNOTATORS[localization['created_by']] if localization[
                'frame': localization['frame'],
                'frame_url': f'/tator/frame/{localization["media"]}/{localization["frame"]}',
                'media_id': localization['media'],
                'phylum': phylogeny[scientific_name]['phylum'] if 'phylum' in phylogeny[
                    scientific_name].keys() else None,
                'subphylum': phylogeny[scientific_name]['subphylum'] if 'subphylum' in phylogeny[
                    scientific_name].keys() else None,
                'superclass': phylogeny[scientific_name]['superclass'] if 'superclass' in phylogeny[
                    scientific_name].keys() else None,
                'class': phylogeny[scientific_name]['class'] if 'class' in phylogeny[scientific_name].keys() else None,
                'subclass': phylogeny[scientific_name]['subclass'] if 'subclass' in phylogeny[
                    scientific_name].keys() else None,
                'superorder': phylogeny[scientific_name]['superorder'] if 'superorder' in phylogeny[
                    scientific_name].keys() else None,
                'order': phylogeny[scientific_name]['order'] if 'order' in phylogeny[scientific_name].keys() else None,
                'suborder': phylogeny[scientific_name]['suborder'] if 'suborder' in phylogeny[
                    scientific_name].keys() else None,
                'infraorder': phylogeny[scientific_name]['infraorder'] if 'infraorder' in phylogeny[
                    scientific_name].keys() else None,
                'superfamily': phylogeny[scientific_name]['superfamily'] if 'superfamily' in phylogeny[
                    scientific_name].keys() else None,
                'family': phylogeny[scientific_name]['family'] if 'family' in phylogeny[
                    scientific_name].keys() else None,
                'subfamily': phylogeny[scientific_name]['subfamily'] if 'subfamily' in phylogeny[
                    scientific_name].keys() else None,
                'genus': phylogeny[scientific_name]['genus'] if 'genus' in phylogeny[scientific_name].keys() else None,
                'species': phylogeny[scientific_name]['species'] if 'species' in phylogeny[
                    scientific_name].keys() else None,
            })

        localization_df = pd.DataFrame(formatted_localizations)

        def collect_localizations(items):
            return [item for item in items]

        localization_df = localization_df.groupby(['media_id', 'frame', 'scientific_name']).agg({
            'id': 'first',
            'all_localizations': collect_localizations,
            'count': 'sum',
            'attracted': 'first',
            'categorical_abundance': 'first',
            'identification_remarks': 'first',
            'identified_by': 'first',
            'notes': 'first',
            'qualifier': 'first',
            'reason': 'first',
            'tentative_id': 'first',
            'video_sequence_name': 'first',
            'annotator': 'first',
            'frame_url': 'first',
            'phylum': 'first',
            'subphylum': 'first',
            'superclass': 'first',
            'class': 'first',
            'subclass': 'first',
            'superorder': 'first',
            'order': 'first',
            'suborder': 'first',
            'infraorder': 'first',
            'superfamily': 'first',
            'family': 'first',
            'subfamily': 'first',
            'genus': 'first',
            'species': 'first',
        }).reset_index()

        localization_df = localization_df.sort_values(by=[
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
            'frame',
            'media_id',
        ])

        for index, row in localization_df.iterrows():
            self.distilled_records.append({
                'observation_uuid': row['id'],
                'all_localizations': row['all_localizations'],
                'media_id': row['media_id'],
                'frame': row['frame'],
                'frame_url': row['frame_url'],
                'annotator': row['annotator'],
                'scientific_name': row['scientific_name'],
                'video_sequence_name': row['video_sequence_name'],
                'count': row['count'],
                'attracted': row['attracted'],
                'categorical_abundance': row['categorical_abundance'],
                'identification_remarks': row['identification_remarks'],
                'identified_by': row['identified_by'],
                'notes': row['notes'],
                'qualifier': row['qualifier'],
                'reason': row['reason'],
                'tentative_id': row['tentative_id'],
                'phylum': row['phylum'],
                'class': row['class'],
                'order': row['order'],
                'family': row['family'],
                'genus': row['genus'],
                'species': row['species'],
            })

        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(phylogeny, f, indent=2)
        except FileNotFoundError:
            os.makedirs('cache')
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(phylogeny, f, indent=2)

        print('processed!')

    def check_names_accepted(self):
        """
        Finds annotations that have more than one of the same association besides s2
        """
        for localization in self.localizations:
            for annotation in self.fetch_annotations(name):
                # get list of associations
                association_set = set()
                duplicate_associations = False
                for association in annotation['associations']:
                    name = association['link_name']
                    if name not in association_set:
                        if name != 's2':
                            association_set.add(name)
                    else:
                        duplicate_associations = True
                        break
                if duplicate_associations:
                    self.working_records.append(annotation)
        self.process_records()
