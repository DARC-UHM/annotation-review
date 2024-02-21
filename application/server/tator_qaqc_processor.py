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
        self.deployment_media_dict = {}
        self.records_of_interest = []
        self.final_records = []
        self.phylogeny = self.load_phylogeny()
        self.localizations = self.fetch_localizations()

    def load_phylogeny(self):
        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_phylogeny(self):
        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(self.phylogeny, f, indent=2)
        except FileNotFoundError:
            os.makedirs('cache')
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(self.phylogeny, f, indent=2)

    def fetch_localizations(self):
        print('Fetching localizations...', end='')
        sys.stdout.flush()
        media_ids = []
        localizations = []
        for deployment in self.deployments:
            for media_id in session[f'{self.project_id}_{self.section_id}'][deployment]:
                self.deployment_media_dict[media_id] = deployment
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
        print(f'fetched {len(localizations)} localizations!')
        return localizations

    def fetch_worms_phylogeny(self, scientific_name: str) -> bool:
        """
        Fetches the phylogeny of a given scientific name from WoRMS. Returns True if successful, False otherwise.
        """
        print(f'Fetching phylogeny for "{scientific_name}"')
        req = requests.get(f'https://www.marinespecies.org/rest/AphiaIDByName/{scientific_name}?marine_only=true')
        if req.status_code == 200 and req.json() != -999:  # -999 means more than one matching record
            aphia_id = req.json()
            req = requests.get(f'https://www.marinespecies.org/rest/AphiaClassificationByAphiaID/{aphia_id}')
            if req.status_code == 200:
                self.phylogeny[scientific_name] = flatten_taxa_tree(req.json(), {})
        else:
            req = requests.get(f'https://www.marinespecies.org/rest/AphiaRecordsByName/{scientific_name}?like=false&marine_only=true&offset=1')
            if req.status_code == 200 and len(req.json()) > 0:
                # just take the first accepted record
                for record in req.json():
                    if record['status'] == 'accepted':
                        req = requests.get(f'https://www.marinespecies.org/rest/AphiaClassificationByAphiaID/{record["AphiaID"]}')
                        if req.status_code == 200:
                            self.phylogeny[scientific_name] = flatten_taxa_tree(req.json(), {})
                        break
            else:
                print(f'{TERM_RED}No accepted record found for concept name "{scientific_name}"{TERM_NORMAL}')
                return False
        return True

    def process_records(self):
        if not self.records_of_interest:
            return
        print('Processing localizations...', end='')
        sys.stdout.flush()

        formatted_localizations = []
        no_match_records = set()

        for localization in self.records_of_interest:
            if localization['type'] not in [48, 49]:
                print('mystery localization skipped...', end='')
                sys.stdout.flush()
                continue
            scientific_name = localization['attributes']['Scientific Name']
            if scientific_name not in self.phylogeny.keys() and scientific_name not in no_match_records:
                if not self.fetch_worms_phylogeny(scientific_name):
                    no_match_records.add(scientific_name)
            localization_dict = {
                'id': localization['id'],
                'all_localizations': {
                    'id': localization['id'],
                    'type': localization['type'],
                    'points': [round(localization['x'], 5), round(localization['y'], 5)],
                    'dimensions': [localization['width'], localization['height']] if localization['type'] == 48 else None,
                },
                'video_sequence_name': self.deployment_media_dict[localization['media']],
                'scientific_name': scientific_name,
                'count': 0 if localization['type'] == 48 else 1,
                'attracted': localization['attributes']['Attracted'] if 'Attracted' in localization['attributes'].keys() else None,
                'categorical_abundance': localization['attributes']['Categorical Abundance'] if 'Categorical Abundance' in localization['attributes'].keys() else None,
                'identification_remarks': localization['attributes']['IdentificationRemarks'] if 'IdentificationRemarks' in localization['attributes'].keys() else None,
                'identified_by': localization['attributes']['Identified By'] if 'Identified By' in localization['attributes'].keys() else None,
                'notes': localization['attributes']['Notes'] if 'Notes' in localization['attributes'].keys() else None,
                'qualifier': localization['attributes']['Qualifier'] if 'Qualifier' in localization['attributes'].keys() else None,
                'reason': localization['attributes']['Reason'] if 'Reason' in localization['attributes'].keys() else None,
                'tentative_id': localization['attributes']['Tentative ID'] if 'Tentative ID' in localization['attributes'].keys() else None,
                'annotator': KNOWN_ANNOTATORS[localization['created_by']] if localization['created_by'] in KNOWN_ANNOTATORS.keys() else f'Unknown Annotator (#{localization["created_by"]})',
                'frame': localization['frame'],
                'frame_url': f'/tator/frame/{localization["media"]}/{localization["frame"]}',
                'media_id': localization['media'],
                'problems': localization['problems'] if 'problems' in localization.keys() else None,
            }
            if scientific_name in self.phylogeny.keys():
                for key in self.phylogeny[scientific_name].keys():
                    localization_dict[key] = self.phylogeny[scientific_name][key]
            formatted_localizations.append(localization_dict)

        self.save_phylogeny()

        if not formatted_localizations:
            print('no records to process!')
            return

        localization_df = pd.DataFrame(formatted_localizations, columns=[
            'id',
            'all_localizations',
            'video_sequence_name',
            'scientific_name',
            'count',
            'attracted',
            'categorical_abundance',
            'identification_remarks',
            'identified_by',
            'notes',
            'qualifier',
            'reason',
            'tentative_id',
            'annotator',
            'frame',
            'frame_url',
            'media_id',
            'problems',
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
        ])

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
            'problems': 'first',
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
            self.final_records.append({
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
                'problems': row['problems'],
            })

        print('processed!')

    def check_names_accepted(self):
        """
        Finds records with a scientific name or tentative ID that is not accepted in WoRMS
        """
        print('Checking for accepted names...')
        sys.stdout.flush()
        checked = {}
        for localization in self.localizations:
            if localization['type'] not in [48, 49]:
                print('Mystery localization skipped')
                sys.stdout.flush()
                continue
            flag_record = False
            scientific_name = localization['attributes']['Scientific Name']
            tentative_id = localization['attributes']['Tentative ID']
            if scientific_name not in checked.keys():
                if scientific_name in self.phylogeny.keys():
                    checked[scientific_name] = True
                else:
                    if self.fetch_worms_phylogeny(scientific_name):
                        checked[scientific_name] = True
                    else:
                        localization['problems'] = 'Scientific Name'
                        checked[scientific_name] = False
                        flag_record = True
            elif not checked[scientific_name]:
                localization['problems'] = 'Scientific Name'
                flag_record = True
            if tentative_id:
                if tentative_id not in checked.keys():
                    if tentative_id in self.phylogeny.keys():
                        checked[tentative_id] = True
                    else:
                        if self.fetch_worms_phylogeny(tentative_id):
                            checked[tentative_id] = True
                        else:
                            localization['problems'] = 'Tentative ID'
                            checked[tentative_id] = False
                            flag_record = True
                elif not checked[tentative_id]:
                    localization['problems'] = 'Tentative ID' if 'problems' not in localization.keys() else 'Scientific Name, Tentative ID'
                    flag_record = True
            if flag_record:
                self.records_of_interest.append(localization)
        print(f'Found {len(self.records_of_interest)} localizations with unaccepted names!')
        self.save_phylogeny()
        self.process_records()
