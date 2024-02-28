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

    def process_records(self, no_match_records: set = None):
        if not self.records_of_interest:
            return
        print('Processing localizations...', end='')
        sys.stdout.flush()

        formatted_localizations = []
        if not no_match_records:
            no_match_records = set()

        for localization in self.records_of_interest:
            if localization['type'] not in [48, 49]:
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
                'attracted': localization['attributes'].get('Attracted'),
                'categorical_abundance': localization['attributes'].get('Categorical Abundance'),
                'identification_remarks': localization['attributes'].get('IdentificationRemarks'),
                'identified_by': localization['attributes'].get('Identified By'),
                'notes': localization['attributes'].get('Notes'),
                'qualifier': localization['attributes'].get('Qualifier'),
                'reason': localization['attributes'].get('Reason'),
                'tentative_id': localization['attributes'].get('Tentative ID'),
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
                'scientific_name': row['scientific_name'] if row['scientific_name'] != '' else '--',
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
        self.process_records(no_match_records={key for key in checked.keys() if not checked[key]})

    def check_missing_qualifier(self):
        """
        Finds records that are classified higher than species but don't have a qualifier set (usually '--'). This check
        need to call process_records first to populate phylogeny.
        """
        self.records_of_interest = self.localizations
        self.process_records()
        actual_final_records = []
        for record in self.final_records:
            if not record['species'] and record['qualifier'] == '--' or not record['qualifier']:
                record['problems'] = 'Scientific Name, Qualifier'
                actual_final_records.append(record)
        self.final_records = actual_final_records

    def check_stet_reason(self):
        """
        Finds records that have a qualifier of 'stet' but no reason set.
        """
        for localization in self.localizations:
            if localization['type'] not in [48, 49]:
                continue
            if localization['attributes']['Qualifier'] == 'stet.' and (
                    localization['attributes']['Reason'] == '--' or not localization['attributes']['Reason']):
                localization['problems'] = 'Qualifier, Reason'
                self.records_of_interest.append(localization)
        self.process_records()

    def check_attracted_not_attracted(self, attracted_dict: dict):
        """
        Finds all records that are marked as "attracted" but are saved as "not attracted" in the attracted_dict, and
        vice versa. Also flags all records with taxa that are marked as "attracted/not attracted" in the attracted_dict.
        """
        for localization in self.localizations:
            scientific_name = localization['attributes']['Scientific Name']
            if scientific_name not in attracted_dict.keys() or attracted_dict[scientific_name] == 2:
                localization['problems'] = 'Scientific Name, Attracted'
                self.records_of_interest.append(localization)
            elif localization['attributes']['Attracted'] == 'Attracted' and attracted_dict[scientific_name] == 0:
                localization['problems'] = 'Scientific Name, Attracted'
                self.records_of_interest.append(localization)
            elif localization['attributes']['Attracted'] == 'Not Attracted' and attracted_dict[scientific_name] == 1:
                localization['problems'] = 'Scientific Name, Attracted'
                self.records_of_interest.append(localization)
        self.process_records()

    def get_all_tentative_ids(self):
        """
        Finds every record with a tentative ID. Also checks whether or not the tentative ID is in the same
        phylogenetic group as the scientific name.
        """
        for localization in self.localizations:
            if localization['type'] not in [48, 49]:
                continue
            tentative_id = localization['attributes']['Tentative ID']
            if tentative_id and tentative_id not in ['--', '-', '']:
                localization['problems'] = 'Tentative ID'
                self.records_of_interest.append(localization)
        self.process_records()  # process first to make sure phylogeny is populated
        for localization in self.final_records:
            phylogeny_match = False
            if localization['tentative_id'] not in self.phylogeny.keys():
                localization['problems'] += ' phylogeny no match'
                continue
            for value in self.phylogeny[localization['scientific_name']].values():
                if value in self.phylogeny[localization['tentative_id']].values():
                    phylogeny_match = True
                    break
            if not phylogeny_match:
                localization['problems'] += ' phylogeny no match'

    def get_all_notes_and_remarks(self):
        """
        Finds every record with a note or remark.
        """
        for localization in self.localizations:
            if localization['type'] not in [48, 49]:
                continue
            notes = localization['attributes']['Notes']
            id_remarks = localization['attributes']['IdentificationRemarks']
            has_note = notes and notes not in ['--', '-', '']
            has_remark = id_remarks and id_remarks not in ['--', '-', '']
            if has_note and has_remark:
                localization['problems'] = 'Notes, ID Remarks'
                self.records_of_interest.append(localization)
            elif has_note:
                localization['problems'] = 'Notes'
                self.records_of_interest.append(localization)
            elif has_remark:
                localization['problems'] = 'ID Remarks'
                self.records_of_interest.append(localization)
        self.process_records()

    def get_unique_taxa(self):
        """
        Finds every unique scientific name and TOFA, max N, and box/dot info.
        """
        for localization in self.localizations:
            if localization['type'] not in [48, 49]:
                continue
            self.records_of_interest.append(localization)
        self.process_records()
        unique_taxa = {}
        for record in self.final_records:
            scientific_name = record['scientific_name']
            if scientific_name not in unique_taxa.keys():
                # add new unique taxa to dict
                unique_taxa[scientific_name] = {
                    'max_n': record['count'],
                    'box_count': 0,
                    'dot_count': 0,
                    'first_box': None,  # todo change once we figure out timestamp stuff
                    'first_dot': None,
                }
            else:
                # check for new max N
                if record['count'] > unique_taxa[scientific_name]['max_n']:
                    unique_taxa[scientific_name]['max_n'] = record['count']
            for localization in record['all_localizations']:
                # increment box/dot counts, set first box/dot and TOFA
                if localization['type'] == 48:
                    unique_taxa[scientific_name]['box_count'] += 1
                    first_box = unique_taxa[scientific_name]['first_box']
                    if (
                        not first_box
                        or int(first_box.split(':')[0]) > record['media_id']
                        or int(first_box.split(':')[0]) == record['media_id'] and int(first_box.split(':')[1]) > record['frame']
                    ):
                        unique_taxa[scientific_name]['first_box'] = f'{record["media_id"]}:{record["frame"]}'
                elif localization['type'] == 49:
                    unique_taxa[scientific_name]['dot_count'] += 1
                    first_dot = unique_taxa[scientific_name]['first_dot']
                    if (
                        not first_dot
                        or int(first_dot.split(':')[0]) > record['media_id']
                        or int(first_dot.split(':')[0]) == record['media_id'] and int(first_dot.split(':')[1]) > record['frame']
                    ):
                        unique_taxa[scientific_name]['first_dot'] = f'{record["media_id"]}:{record["frame"]}'
        self.final_records = unique_taxa
