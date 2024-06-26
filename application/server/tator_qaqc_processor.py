import json
import math

import pandas as pd
import os
import requests
import sys
import tator

from datetime import timezone
from flask import session
from io import BytesIO
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from .constants import KNOWN_ANNOTATORS
from .functions import *

TERM_RED = '\033[1;31;48m'
TERM_NORMAL = '\033[1;37;0m'


class TatorQaqcProcessor:
    """
    Fetches annotation information from the Tator given a project id, section id, and list of deployments.
    Filters and formats the annotations for the various QA/QC checks.
    """
    def __init__(self, project_id: int, section_id: int, api: tator.api, deployment_list: list, darc_review_url: str = None):
        self.project_id = project_id
        self.section_id = section_id
        self.api = api
        self.deployments = deployment_list
        self.bottom_times = {deployment: '' for deployment in deployment_list}
        self.deployment_media_dict = {}
        self.darc_review_url = darc_review_url
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

    def fetch_start_times(self):
        for deployment in self.deployments:
            print(f'Fetching media start times for deployment "{deployment}"...', end='')
            sys.stdout.flush()
            if 'media_timestamps' not in session.keys():
                session['media_timestamps'] = {}
            res = requests.get(
                url=f'https://cloud.tator.io/rest/Medias/{self.project_id}?section={self.section_id}&attribute_contains=%24name%3A%3A{deployment}',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Token {session["tator_token"]}',
                }
            )
            for media in res.json():
                if media['attributes']['Arrival'] and media['attributes']['Arrival'].strip() != '':
                    video_start_timestamp = datetime.fromisoformat(media['attributes']['Start Time'])
                    if 'not observed' in media['attributes']['Arrival']:
                        arrival_frame = 0
                    else:
                        try:
                            arrival_frame = int(media['attributes']['Arrival'].strip().split(' ')[0])
                        except ValueError:
                            print(f'\n{TERM_RED}Error:{TERM_NORMAL} Could not parse Arrival value for {media["name"]}')
                            print(f'Arrival value: "{media["attributes"]["Arrival"]}"')
                            raise ValueError
                    self.bottom_times[deployment] = (video_start_timestamp + timedelta(seconds=arrival_frame / 30)).strftime('%Y-%m-%d %H:%M:%SZ')
                if media['id'] not in session['media_timestamps'].keys():
                    if 'Start Time' in media['attributes'].keys():
                        session['media_timestamps'][media['id']] = media['attributes']['Start Time']
                        session.modified = True
                    else:
                        print(f'{TERM_RED}Warning:{TERM_NORMAL} No start time found for media {media["id"]}')
            print('fetched!')

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
            res = requests.get(
                url=f'https://cloud.tator.io/rest/Localizations/{self.project_id}?media_id={",".join(map(str, chunk))}',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Token {session["tator_token"]}',
                })
            localizations += res.json()
        print(f'fetched {len(localizations)} localizations!')
        return localizations

    def fetch_worms_phylogeny(self, scientific_name: str) -> bool:
        """
        Fetches the phylogeny of a given scientific name from WoRMS. Returns True if successful, False otherwise.
        """
        print(f'Fetching phylogeny for "{scientific_name}"')
        worms_id_res = requests.get(url=f'https://www.marinespecies.org/rest/AphiaIDByName/{scientific_name}?marine_only=true')
        if worms_id_res.status_code == 200 and worms_id_res.json() != -999:  # -999 means more than one matching record
            aphia_id = worms_id_res.json()
            worms_tree_res = requests.get(url=f'https://www.marinespecies.org/rest/AphiaClassificationByAphiaID/{aphia_id}')
            if worms_tree_res.status_code == 200:
                self.phylogeny[scientific_name] = flatten_taxa_tree(worms_tree_res.json(), {})
                self.phylogeny[scientific_name]['aphia_id'] = aphia_id
        else:
            worms_name_res = requests.get(url=f'https://www.marinespecies.org/rest/AphiaRecordsByName/{scientific_name}?like=false&marine_only=true&offset=1')
            if worms_name_res.status_code == 200 and len(worms_name_res.json()) > 0:
                # just take the first accepted record
                for record in worms_name_res.json():
                    if record['status'] == 'accepted':
                        worms_tree_res_2 = requests.get(url=f'https://www.marinespecies.org/rest/AphiaClassificationByAphiaID/{record["AphiaID"]}')
                        if worms_tree_res_2.status_code == 200:
                            self.phylogeny[scientific_name] = flatten_taxa_tree(worms_tree_res_2.json(), {})
                            self.phylogeny[scientific_name]['aphia_id'] = record['AphiaID']
                        break
            else:
                print(f'{TERM_RED}No accepted record found for concept name "{scientific_name}"{TERM_NORMAL}')
                return False
        return True

    def process_records(self, no_match_records: set = None, get_timestamp: bool = False, get_ctd: bool = False, get_substrates: bool = False):
        if not self.records_of_interest:
            return
        print('Processing localizations...', end='')
        sys.stdout.flush()

        formatted_localizations = []
        expedition_fieldbook = []
        deployment_substrates = {}

        if not no_match_records:
            no_match_records = set()

        if get_ctd:
            fieldbook = requests.get(
                url=f'{self.darc_review_url}/dropcam-fieldbook/{self.section_id}',
                headers={'API-Key': os.environ.get('DARC_REVIEW_API_KEY')},
            )
            if fieldbook.status_code == 200:
                expedition_fieldbook = fieldbook.json()['deployments']
            else:
                print(f'{TERM_RED}Error fetching expedition fieldbook.{TERM_NORMAL}')

        if get_substrates:
            for deployment in self.deployments:
                deployment_substrates[deployment] = self.api.get_media_list(
                    project=self.project_id,
                    section=self.section_id,
                    attribute_contains=[f'$name::{deployment}'],
                    stop=1,
                )[0].attributes

        for localization in self.records_of_interest:
            if localization['type'] not in [48, 49]:
                continue
            scientific_name = localization['attributes']['Scientific Name']
            if scientific_name not in self.phylogeny.keys() and scientific_name not in no_match_records:
                if not self.fetch_worms_phylogeny(scientific_name):
                    no_match_records.add(scientific_name)
            localization_dict = {
                'elemental_id': localization['elemental_id'],
                'all_localizations': {
                    'id': localization['id'],
                    'elemental_id': localization['elemental_id'],
                    'version': localization['version'],
                    'type': localization['type'],
                    'points': [round(localization['x'], 5), round(localization['y'], 5)],
                    'dimensions': [localization['width'], localization['height']] if localization['type'] == 48 else None,
                },
                'type': localization['type'],
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
                'good_image': localization['attributes'].get('Good Image'),
                'annotator': KNOWN_ANNOTATORS[localization['created_by']] if localization['created_by'] in KNOWN_ANNOTATORS.keys() else f'Unknown Annotator (#{localization["created_by"]})',
                'frame': localization['frame'],
                'frame_url': f'/tator/frame/{localization["media"]}/{localization["frame"]}',
                'media_id': localization['media'],
                'problems': localization['problems'] if 'problems' in localization.keys() else None,
            }
            if localization_dict['categorical_abundance'] and localization_dict['categorical_abundance'] != '--':
                match localization_dict['categorical_abundance']:
                    case '1-19':
                        localization_dict['count'] = 10
                    case '20-49':
                        localization_dict['count'] = 35
                    case '50-99':
                        localization_dict['count'] = 75
                    case '100-999':
                        localization_dict['count'] = 500
                    case '1000+':
                        localization_dict['count'] = 1000
                    case _:
                        print(f'{TERM_RED}Unknown categorical abundance: {localization_dict["categorical_abundance"]}{TERM_NORMAL}')
            if get_timestamp:
                if localization['media'] in session['media_timestamps'].keys():
                    camera_bottom_arrival = datetime.strptime(
                        self.bottom_times[self.deployment_media_dict[localization['media']]],
                        '%Y-%m-%d %H:%M:%SZ'
                    ).replace(tzinfo=timezone.utc)
                    video_start_timestamp = datetime.fromisoformat(session['media_timestamps'][localization['media']])
                    observation_timestamp = video_start_timestamp + timedelta(seconds=localization['frame'] / 30)
                    time_diff = observation_timestamp - camera_bottom_arrival
                    localization_dict['timestamp'] = observation_timestamp.strftime('%Y-%m-%d %H:%M:%SZ')
                    localization_dict['camera_seafloor_arrival'] = camera_bottom_arrival.strftime('%Y-%m-%d %H:%M:%SZ')
                    localization_dict['animal_arrival'] = str(timedelta(
                        days=time_diff.days,
                        seconds=time_diff.seconds
                    )) if observation_timestamp > camera_bottom_arrival else '00:00:00'
            if get_ctd and expedition_fieldbook:
                localization_dict['do_temp_c'] = localization['attributes'].get('DO Temperature (celsius)')
                localization_dict['do_concentration_salin_comp_mol_L'] = localization['attributes'].get('DO Concentration Salin Comp (mol per L)')
                deployment_name = self.deployment_media_dict[localization['media']]
                deployment_ctd = next((x for x in expedition_fieldbook if x['deployment_name'] == deployment_name.replace('-', '_')), None)
                if deployment_ctd:
                    localization_dict['lat'] = deployment_ctd['lat']
                    localization_dict['long'] = deployment_ctd['long']
                    localization_dict['depth_m'] = deployment_ctd['depth_m']
                    localization_dict['bait_type'] = deployment_ctd['bait_type']
            if get_substrates and deployment_substrates:
                localization_dict['primary_substrate'] = deployment_substrates[self.deployment_media_dict[localization['media']]]['Primary Substrate']
                localization_dict['secondary_substrate'] = deployment_substrates[self.deployment_media_dict[localization['media']]]['Secondary Substrate']
                localization_dict['bedforms'] = deployment_substrates[self.deployment_media_dict[localization['media']]]['Bedforms']
                localization_dict['relief'] = deployment_substrates[self.deployment_media_dict[localization['media']]]['Relief']
                localization_dict['substrate_notes'] = deployment_substrates[self.deployment_media_dict[localization['media']]]['Substrate Notes']
            if scientific_name in self.phylogeny.keys():
                for key in self.phylogeny[scientific_name].keys():
                    # split to account for worms 'Phylum (Division)' case
                    localization_dict[key.split(' ')[0]] = self.phylogeny[scientific_name][key]
            formatted_localizations.append(localization_dict)

        self.save_phylogeny()

        if not formatted_localizations:
            print('no records to process!')
            return

        localization_df = pd.DataFrame(formatted_localizations, columns=[
            'elemental_id',
            'timestamp',
            'camera_seafloor_arrival',
            'animal_arrival',
            'all_localizations',
            'type',
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
            'good_image',
            'annotator',
            'frame',
            'frame_url',
            'media_id',
            'problems',
            'lat',
            'long',
            'depth_m',
            'do_temp_c',
            'do_concentration_salin_comp_mol_L',
            'bait_type',
            'primary_substrate',
            'secondary_substrate',
            'bedforms',
            'relief',
            'substrate_notes',
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
            'subgenus',
            'species',
            'subspecies',
            'aphia_id',
        ])

        def collect_localizations(items):
            return [item for item in items]

        localization_df = localization_df.groupby(['media_id', 'frame', 'scientific_name', 'tentative_id', 'type']).agg({
            'elemental_id': 'first',
            'timestamp': 'first',
            'camera_seafloor_arrival': 'first',
            'animal_arrival': 'first',
            'all_localizations': collect_localizations,
            'count': 'sum',
            'attracted': 'first',
            'categorical_abundance': 'first',
            'identification_remarks': 'first',
            'identified_by': 'first',
            'notes': 'first',
            'qualifier': 'first',
            'reason': 'first',
            'good_image': 'first',
            'video_sequence_name': 'first',
            'annotator': 'first',
            'frame_url': 'first',
            'problems': 'first',
            'lat': 'first',
            'long': 'first',
            'depth_m': 'first',
            'do_temp_c': 'first',
            'do_concentration_salin_comp_mol_L': 'first',
            'bait_type': 'first',
            'primary_substrate': 'first',
            'secondary_substrate': 'first',
            'bedforms': 'first',
            'relief': 'first',
            'substrate_notes': 'first',
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
            'subgenus': 'first',
            'species': 'first',
            'subspecies': 'first',
            'aphia_id': 'first',
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
            'media_id',
            'frame',
        ])

        for index, row in localization_df.iterrows():
            self.final_records.append({
                'observation_uuid': row['elemental_id'],
                'timestamp': row['timestamp'],
                'camera_seafloor_arrival': row['camera_seafloor_arrival'],
                'animal_arrival': row['animal_arrival'],
                'all_localizations': row['all_localizations'],
                'media_id': row['media_id'],
                'frame': row['frame'],
                'frame_url': row['frame_url'],
                'annotator': row['annotator'],
                'scientific_name': row['scientific_name'] if row['scientific_name'] != '' else '--',
                'section_id': self.section_id,
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
                'good_image': row['good_image'],
                'problems': row['problems'],
                'lat': row['lat'],
                'long': row['long'],
                'depth_m': row['depth_m'],
                'do_temp_c': row['do_temp_c'],
                'do_concentration_salin_comp_mol_L': row['do_concentration_salin_comp_mol_L'],
                'bait_type': row['bait_type'],
                'primary_substrate': row['primary_substrate'],
                'secondary_substrate': row['secondary_substrate'],
                'bedforms': row['bedforms'],
                'relief': row['relief'],
                'substrate_notes': row['substrate_notes'],
                'phylum': row['phylum'],
                'subphylum': row['subphylum'],
                'superclass': row['superclass'],
                'class': row['class'],
                'subclass': row['subclass'],
                'superorder': row['superorder'],
                'order': row['order'],
                'suborder': row['suborder'],
                'infraorder': row['infraorder'],
                'superfamily': row['superfamily'],
                'family': row['family'],
                'subfamily': row['subfamily'],
                'genus': row['genus'],
                'subgenus': row['subgenus'],
                'species': row['species'],
                'subspecies': row['subspecies'],
                'aphia_id': row['aphia_id'],
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

    def check_same_name_qualifier(self):
        """
        Finds records that have the same scientific name/tentative ID combo but a different qualifier.
        """
        scientific_name_qualifiers = {}
        problem_scientific_names = set()
        for localization in self.localizations:
            scientific_name = f'{localization["attributes"]["Scientific Name"]}{" (" + localization["attributes"]["Tentative ID"] + "?)" if localization["attributes"]["Tentative ID"] else ""}'
            if scientific_name not in scientific_name_qualifiers.keys():
                scientific_name_qualifiers[scientific_name] = localization['attributes']['Qualifier']
            else:
                if scientific_name_qualifiers[scientific_name] != localization['attributes']['Qualifier']:
                    problem_scientific_names.add(scientific_name)
        for localization in self.localizations:
            scientific_name = f'{localization["attributes"]["Scientific Name"]}{" (" + localization["attributes"]["Tentative ID"] + "?)" if localization["attributes"]["Tentative ID"] else ""}'
            if scientific_name in problem_scientific_names:
                localization['problems'] = 'Scientific Name, Qualifier'
                self.records_of_interest.append(localization)
        self.process_records()

    def check_non_target_not_attracted(self):
        """
        Finds records that are marked as "non-target" but are marked as "attracted".
        """
        for localization in self.localizations:
            attracted = localization['attributes']['Attracted']
            reason = localization['attributes']['Reason']
            if 'Non-target' in reason and attracted != 'Not Attracted':
                localization['problems'] = 'Attracted, Reason'
                self.records_of_interest.append(localization)
        self.process_records()

    def get_all_tentative_ids(self):
        """
        Finds every record with a tentative ID. Also checks whether or not the tentative ID is in the same
        phylogenetic group as the scientific name.
        """
        no_match_records = set()
        for localization in self.localizations:
            tentative_id = localization['attributes']['Tentative ID']
            if tentative_id and tentative_id not in ['--', '-', '']:
                localization['problems'] = 'Tentative ID'
                self.records_of_interest.append(localization)
        self.process_records()  # process first to make sure phylogeny is populated
        for localization in self.final_records:
            phylogeny_match = False
            if localization['tentative_id'] not in self.phylogeny.keys():
                if localization['tentative_id'] not in no_match_records:
                    if not self.fetch_worms_phylogeny(localization['tentative_id']):
                        no_match_records.add(localization['tentative_id'])
                        localization['problems'] += ' phylogeny no match'
                        continue
                else:
                    localization['problems'] += ' phylogeny no match'
                    continue
            for value in self.phylogeny[localization['tentative_id']].values():
                if value == localization['scientific_name']:
                    phylogeny_match = True
                    break
            if not phylogeny_match:
                localization['problems'] += ' phylogeny no match'
        self.save_phylogeny()

    def get_all_notes_and_remarks(self):
        """
        Finds every record with a note or remark.
        """
        for localization in self.localizations:
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
        Finds every unique scientific name/tentative ID combo and box/dot info.
        """
        self.fetch_start_times()
        self.records_of_interest = self.localizations
        self.process_records(get_timestamp=True)
        unique_taxa = {}
        for record in self.final_records:
            scientific_name = record['scientific_name']
            tentative_id = record['tentative_id']
            key = f'{scientific_name}:{tentative_id}'
            if key not in unique_taxa.keys():
                # add new unique taxa to dict
                unique_taxa[key] = {
                    'scientific_name': scientific_name,
                    'tentative_id': tentative_id,
                    'box_count': 0,
                    'dot_count': 0,
                    'first_box': '',
                    'first_dot': '',
                }
            for localization in record['all_localizations']:
                # increment box/dot counts, set first box/dot and TOFA
                if localization['type'] == 48:
                    unique_taxa[key]['box_count'] += 1
                    first_box = unique_taxa[key]['first_box']
                    if not first_box or datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%SZ') < datetime.strptime(first_box, '%Y-%m-%d %H:%M:%SZ'):
                        unique_taxa[key]['first_box'] = record['timestamp']
                        unique_taxa[key]['first_box_url'] = f'https://cloud.tator.io/{self.project_id}/annotation/{record["media_id"]}?frame={record["frame"]}&selected_entity={localization["elemental_id"]}'
                elif localization['type'] == 49:
                    unique_taxa[key]['dot_count'] += 1
                    first_dot = unique_taxa[key]['first_dot']
                    observed_timestamp = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%SZ')
                    if not first_dot or observed_timestamp < datetime.strptime(first_dot, '%Y-%m-%d %H:%M:%SZ'):
                        unique_taxa[key]['first_dot'] = record['timestamp']
                        unique_taxa[key]['first_dot_url'] = f'https://cloud.tator.io/{self.project_id}/annotation/{record["media_id"]}?frame={record["frame"]}&selected_entity={localization["elemental_id"]}'
        self.final_records = unique_taxa

    def get_max_n(self):
        """
        Finds the highest dot count for each unique scientific name/tentative ID combo per deployment.
        """
        self.records_of_interest = self.localizations
        self.process_records(get_ctd=True)
        deployment_taxa = {}
        unique_taxa = {}
        for record in self.final_records:
            scientific_tentative = f'{record["scientific_name"]}{" (" + record["tentative_id"] + "?)" if record["tentative_id"] else ""}'
            if record['count'] < 1 or record['attracted'] == 'Not Attracted':
                continue
            if scientific_tentative not in unique_taxa.keys():
                unique_taxa[scientific_tentative] = {
                    'scientific_tentative': scientific_tentative,
                    'phylum': record.get('phylum'),
                    'class': record.get('class'),
                    'order': record.get('order'),
                    'family': record.get('family'),
                    'genus': record.get('genus'),
                    'species': record.get('species'),
                }
            if record['video_sequence_name'] not in deployment_taxa.keys():
                deployment_taxa[record['video_sequence_name']] = {
                    'depth_m': record['depth_m'],
                    'max_n_dict': {},
                }
            if scientific_tentative not in deployment_taxa[record['video_sequence_name']]['max_n_dict'].keys():
                # add new unique taxa to dict
                deployment_taxa[record['video_sequence_name']]['max_n_dict'][scientific_tentative] = {
                    'max_n': record['count'],
                    'max_n_url': f'https://cloud.tator.io/{self.project_id}/annotation/{record["media_id"]}?frame={record["frame"]}',
                }
            else:
                # check for new max N
                if record['count'] > deployment_taxa[record['video_sequence_name']]['max_n_dict'][scientific_tentative]['max_n']:
                    deployment_taxa[record['video_sequence_name']]['max_n_dict'][scientific_tentative]['max_n'] = record['count']
                    deployment_taxa[record['video_sequence_name']]['max_n_dict'][scientific_tentative]['max_n_url'] = f'https://cloud.tator.io/{self.project_id}/annotation/{record["media_id"]}?frame={record["frame"]}'
        # convert unique taxa to list for sorting
        unique_taxa_list = list(unique_taxa.values())
        unique_taxa_list.sort(key=lambda x: (
            x['phylum'] if x.get('phylum') else '',
            x['class'] if x.get('class') else '',
            x['order'] if x.get('order') else '',
            x['family'] if x.get('family') else '',
            x['genus'] if x.get('genus') else '',
            x['species'] if x.get('species') else '',
        ))
        self.final_records = {'deployments': deployment_taxa, 'unique_taxa': [taxa['scientific_tentative'] for taxa in unique_taxa_list]}

    def get_tofa(self):
        """
        Finds the time of first arrival for each unique scientific name/tentative ID combo per deployment. Also shows
        species accumulation curve. Ignores non-attracted taxa.
        """
        self.fetch_start_times()
        self.records_of_interest = self.localizations
        self.process_records(get_timestamp=True, get_ctd=True)
        deployment_taxa = {}
        unique_taxa = {}
        unique_taxa_first_seen = {}
        bottom_time = None
        latest_timestamp = datetime.fromtimestamp(0)  # to find the duration of the deployment
        for record in self.final_records:
            scientific_tentative = f'{record["scientific_name"]}{" (" + record["tentative_id"] + "?)" if record["tentative_id"] else ""}'
            observed_timestamp = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%SZ')
            bottom_time = datetime.strptime(self.bottom_times[record['video_sequence_name']], '%Y-%m-%d %H:%M:%SZ')
            if record['count'] < 1 or record['attracted'] == 'Not Attracted':
                continue
            if observed_timestamp > latest_timestamp:
                latest_timestamp = observed_timestamp
            if scientific_tentative not in unique_taxa_first_seen.keys():
                unique_taxa_first_seen[scientific_tentative] = observed_timestamp
            else:
                if observed_timestamp < unique_taxa_first_seen[scientific_tentative]:
                    unique_taxa_first_seen[scientific_tentative] = observed_timestamp
            if scientific_tentative not in unique_taxa.keys():
                unique_taxa[scientific_tentative] = {
                    'scientific_tentative': scientific_tentative,
                    'phylum': record.get('phylum'),
                    'class': record.get('class'),
                    'order': record.get('order'),
                    'family': record.get('family'),
                    'genus': record.get('genus'),
                    'species': record.get('species'),
                }
            if record['video_sequence_name'] not in deployment_taxa.keys():
                deployment_taxa[record['video_sequence_name']] = {
                    'depth_m': record['depth_m'],
                    'tofa_dict': {},
                }
            if scientific_tentative not in deployment_taxa[record['video_sequence_name']]['tofa_dict'].keys():
                # add new unique taxa to dict
                deployment_taxa[record['video_sequence_name']]['tofa_dict'][scientific_tentative] = {
                    'tofa': str(observed_timestamp - bottom_time) if observed_timestamp > bottom_time else '00:00:00',
                    'tofa_url': f'https://cloud.tator.io/{self.project_id}/annotation/{record["media_id"]}?frame={record["frame"]}',
                }
            else:
                # check for new tofa
                if str(observed_timestamp - bottom_time) < deployment_taxa[record['video_sequence_name']]['tofa_dict'][scientific_tentative]['tofa']:
                    deployment_taxa[record['video_sequence_name']]['tofa_dict'][scientific_tentative]['tofa'] = str(observed_timestamp - bottom_time) if observed_timestamp > bottom_time else '00:00:00'
                    deployment_taxa[record['video_sequence_name']]['tofa_dict'][scientific_tentative]['tofa_url'] = f'https://cloud.tator.io/{self.project_id}/annotation/{record["media_id"]}?frame={record["frame"]}'
        # convert unique taxa to list for sorting
        unique_taxa_list = list(unique_taxa.values())
        unique_taxa_list.sort(key=lambda x: (
            x['phylum'] if x.get('phylum') else '',
            x['class'] if x.get('class') else '',
            x['order'] if x.get('order') else '',
            x['family'] if x.get('family') else '',
            x['genus'] if x.get('genus') else '',
            x['species'] if x.get('species') else '',
        ))
        # rounding up to nearest hour
        deployment_time = timedelta(hours=math.ceil((latest_timestamp - bottom_time).total_seconds() / 3600))
        accumulation_data = []  # just a list of the number of unique taxa seen at each hour
        for hour in range(1, deployment_time.seconds // 3600 + 1):
            accumulation_data.append(len([taxa for taxa in unique_taxa_first_seen.values() if taxa < bottom_time + timedelta(hours=hour)]))
        self.final_records = {
            'deployments': deployment_taxa,
            'unique_taxa': [taxa['scientific_tentative'] for taxa in unique_taxa_list],
            'deployment_time': deployment_time.seconds // 3600,
            'accumulation_data': accumulation_data,
        }

    def get_summary(self):
        """
        Returns a summary of the final records.
        """
        self.fetch_start_times()
        self.records_of_interest = [localization for localization in self.localizations if localization['type'] != 48]
        self.process_records(get_timestamp=True, get_ctd=True, get_substrates=True)

    def download_image_guide(self, app) -> Presentation:
        """
        Finds all records marked as "good" images, saves them to a ppt.
        """
        for localization in self.localizations:
            if localization['attributes'].get('Good Image'):
                self.records_of_interest.append(localization)
        self.process_records()
        pres = Presentation()
        image_slide_layout = pres.slide_layouts[6]

        i = 0
        while i < len(self.final_records):
            slide = pres.slides.add_slide(image_slide_layout)
            current_phylum = self.final_records[i].get('phylum')
            if current_phylum is None:
                current_phylum = 'UNKNOWN PHYLUM'
            phylum_text_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(9), Inches(0.5))
            phylum_text_frame = phylum_text_box.text_frame
            phylum_paragraph = phylum_text_frame.paragraphs[0]
            phylum_paragraph.alignment = PP_ALIGN.CENTER
            phylum_run = phylum_paragraph.add_run()
            phylum_run.text = ' '.join(list(current_phylum.upper()))
            phylum_font = phylum_run.font
            phylum_font.name = 'Arial'
            phylum_font.size = Pt(32)
            phylum_font.color.rgb = RGBColor(0, 0, 0)
            for j in range(4):
                # add four images to slide
                localization = self.final_records[i]
                if localization['phylum'] != current_phylum and current_phylum != 'UNKNOWN PHYLUM':
                    break
                localization_id = localization['all_localizations'][0]['id']
                response = requests.get(f'{app.config.get("LOCAL_APP_URL")}/tator-localization/{localization_id}?token={session["tator_token"]}')
                if response.status_code != 200:
                    print(f'Error fetching image for record {localization["observation_uuid"]}')
                    continue
                image_data = BytesIO(response.content)
                top = Inches(1.5 if j < 2 else 4)
                left = Inches(1 if j % 2 == 0 else 5)
                picture = slide.shapes.add_picture(image_data, left, top, height=Inches(2.5))
                line = picture.line
                line.color.rgb = RGBColor(0, 0, 0)
                line.width = Pt(1.5)
                # add text box
                width = Inches(2)
                height = Inches(1)
                text_box = slide.shapes.add_textbox(left, top, width, height)
                text_frame = text_box.text_frame
                paragraph = text_frame.paragraphs[0]
                run = paragraph.add_run()
                run.text = f'{localization["scientific_name"]}{" (" + localization["tentative_id"] + "?)" if localization.get("tentative_id") else ""}'
                font = run.font
                font.name = 'Arial'
                font.size = Pt(18)
                font.color.rgb = RGBColor(0xff, 0xff, 0xff)
                font.italic = True
                if localization['attracted'] == 'Not Attracted':
                    text_frame.add_paragraph()
                    paragraph = text_frame.paragraphs[1]
                    run_2 = paragraph.add_run()
                    run_2.text = 'NOT ATTRACTED'
                    font = run_2.font
                    font.name = 'Arial'
                    font.size = Pt(18)
                    font.color.rgb = RGBColor(0xff, 0x0, 0x0)
                    font.italic = False
                i += 1
                if i >= len(self.final_records):
                    break
        return pres
