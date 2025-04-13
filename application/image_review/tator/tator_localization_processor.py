import datetime
import json
import os
import pandas as pd
import requests
import sys
import tator

from flask import session
from application.util.constants import KNOWN_ANNOTATORS, TERM_RED, TERM_NORMAL
from application.util.tator_localization_type import TatorLocalizationType
from application.util.functions import flatten_taxa_tree

WORMS_REST_URL = 'https://www.marinespecies.org/rest'


class TatorLocalizationProcessor:
    """
    Fetches all localization information for a given project/section/deployment list from Tator. Processes
    and sorts data for display on the image review pages.
    """

    def __init__(
        self,
        project_id: int,
        section_id: int,
        api: tator.api,
        deployment_list: list,
        tator_url: str,
        darc_review_url: str = None,
    ):
        self.project_id = project_id
        self.section_id = section_id
        self.api = api
        self.deployments = deployment_list
        self.tator_url = tator_url
        self.darc_review_url = darc_review_url
        self.localizations = []  # list of raw localizations from tator
        self.final_records = []  # final list formatted for review page
        self.deployment_media_dict = {}  # dict of all relevant media ids and their dep names
        self.bottom_times = {deployment: '' for deployment in deployment_list}
        self.phylogeny = {}
        self.section_name = self.api.get_section(section_id).name

    def load_phylogeny(self):
        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'r') as f:
                self.phylogeny = json.load(f)
        except FileNotFoundError:
            self.phylogeny = {}

    def save_phylogeny(self):
        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(self.phylogeny, f, indent=2)
        except FileNotFoundError:
            os.makedirs('cache')
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(self.phylogeny, f, indent=2)

    def fetch_worms_phylogeny(self, scientific_name: str) -> bool:
        """
        Fetches the phylogeny of a given scientific name from WoRMS. Returns True if successful, False otherwise.
        """
        print(f'Fetching phylogeny for "{scientific_name}"')
        worms_id_res = requests.get(url=f'{WORMS_REST_URL}/AphiaIDByName/{scientific_name}?marine_only=true')
        if worms_id_res.status_code == 200 and worms_id_res.json() != -999:  # -999 means more than one matching record
            aphia_id = worms_id_res.json()
            worms_tree_res = requests.get(url=f'{WORMS_REST_URL}/AphiaClassificationByAphiaID/{aphia_id}')
            if worms_tree_res.status_code == 200:
                self.phylogeny[scientific_name] = flatten_taxa_tree(worms_tree_res.json(), {})
                self.phylogeny[scientific_name]['aphia_id'] = aphia_id
        else:
            worms_name_res = requests.get(url=f'{WORMS_REST_URL}/AphiaRecordsByName/{scientific_name}?like=false&marine_only=true&offset=1')
            if worms_name_res.status_code == 200 and len(worms_name_res.json()) > 0:
                # just take the first accepted record
                for record in worms_name_res.json():
                    if record['status'] == 'accepted':
                        worms_tree_res_2 = requests.get(url=f'{WORMS_REST_URL}/AphiaClassificationByAphiaID/{record["AphiaID"]}')
                        if worms_tree_res_2.status_code == 200:
                            self.phylogeny[scientific_name] = flatten_taxa_tree(worms_tree_res_2.json(), {})
                            self.phylogeny[scientific_name]['aphia_id'] = record['AphiaID']
                        break
            else:
                print(f'{TERM_RED}No accepted record found for concept name "{scientific_name}"{TERM_NORMAL}')
                return False
        return True

    def fetch_localizations(self):
        print('Fetching localizations...', end='')
        sys.stdout.flush()
        media_ids = []
        for deployment in self.deployments:
            for media_id in session[f'{self.project_id}_{self.section_id}'][deployment]:
                self.deployment_media_dict[media_id] = deployment
            media_ids += session[f'{self.project_id}_{self.section_id}'][deployment]
        # REST is much faster than Python API for large queries
        # adding too many media ids results in a query that is too long, so we have to break it up
        for i in range(0, len(media_ids), 300):
            chunk = media_ids[i:i + 300]
            res = requests.get(
                url=f'{self.tator_url}/rest/Localizations/{self.project_id}?media_id={",".join(map(str, chunk))}',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Token {session["tator_token"]}',
                })
            self.localizations += res.json()
        print(f'fetched {len(self.localizations)} localizations!')

    def process_records(
        self,
        no_match_records: set = None,
        get_timestamp: bool = False,
        get_ctd: bool = False,
        get_substrates: bool = False,
    ):
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

        for localization in self.localizations:
            if localization['type'] not in [TatorLocalizationType.BOX.value, TatorLocalizationType.DOT.value]:
                continue  # we only care about boxes and dots
            scientific_name = localization['attributes'].get('Scientific Name')
            cached_phylogeny = self.phylogeny.get(scientific_name)
            if (cached_phylogeny is None or 'aphia_id' not in cached_phylogeny.keys())\
                    and scientific_name not in no_match_records:
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
                    'dimensions': [localization['width'], localization['height']]
                    if localization['type'] == TatorLocalizationType.BOX.value
                    else None,
                },
                'type': localization['type'],
                'video_sequence_name': self.deployment_media_dict[localization['media']],
                'scientific_name': scientific_name,
                'count': 0 if localization['type'] == TatorLocalizationType.BOX.value else 1,
                'attracted': localization['attributes'].get('Attracted'),
                'categorical_abundance': localization['attributes'].get('Categorical Abundance'),
                'identification_remarks': localization['attributes'].get('IdentificationRemarks'),
                'identified_by': localization['attributes'].get('Identified By'),
                'notes': localization['attributes'].get('Notes'),
                'qualifier': localization['attributes'].get('Qualifier'),
                'reason': localization['attributes'].get('Reason'),
                'morphospecies': localization['attributes'].get('Morphospecies'),
                'tentative_id': localization['attributes'].get('Tentative ID'),
                'good_image': True if localization['attributes'].get('Good Image') else False,
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
                    camera_bottom_arrival = datetime.datetime.strptime(
                        self.bottom_times[self.deployment_media_dict[localization['media']]],
                        '%Y-%m-%d %H:%M:%SZ'
                    ).replace(tzinfo=datetime.timezone.utc)
                    video_start_timestamp = datetime.datetime.fromisoformat(session['media_timestamps'][localization['media']])
                    observation_timestamp = video_start_timestamp + datetime.timedelta(seconds=localization['frame'] / 30)
                    time_diff = observation_timestamp - camera_bottom_arrival
                    localization_dict['timestamp'] = observation_timestamp.strftime('%Y-%m-%d %H:%M:%SZ')
                    localization_dict['camera_seafloor_arrival'] = camera_bottom_arrival.strftime('%Y-%m-%d %H:%M:%SZ')
                    localization_dict['animal_arrival'] = str(datetime.timedelta(
                        days=time_diff.days,
                        seconds=time_diff.seconds
                    )) if observation_timestamp > camera_bottom_arrival else '00:00:00'
            if get_ctd and expedition_fieldbook:
                localization_dict['do_temp_c'] = localization['attributes'].get('DO Temperature (celsius)')
                localization_dict['do_concentration_salin_comp_mol_L'] = localization['attributes'].get('DO Concentration Salin Comp (mol per L)')
                localization_dict['depth_m'] = localization['attributes'].get('Depth')
                deployment_name = self.deployment_media_dict[localization['media']]
                deployment_name = deployment_name.replace('-', '_')  # for DOEX0087_NIU-dscm-02
                deployment_ctd = next((x for x in expedition_fieldbook if x['deployment_name'] == deployment_name.replace('-', '_')), None)
                if deployment_ctd:
                    localization_dict['lat'] = deployment_ctd['lat']
                    localization_dict['long'] = deployment_ctd['long']
                    localization_dict['bait_type'] = deployment_ctd['bait_type']
            if get_substrates and deployment_substrates:
                localization_dict['primary_substrate'] = deployment_substrates[self.deployment_media_dict[localization['media']]].get('Primary Substrate')
                localization_dict['secondary_substrate'] = deployment_substrates[self.deployment_media_dict[localization['media']]].get('Secondary Substrate')
                localization_dict['bedforms'] = deployment_substrates[self.deployment_media_dict[localization['media']]].get('Bedforms')
                localization_dict['relief'] = deployment_substrates[self.deployment_media_dict[localization['media']]].get('Relief')
                localization_dict['substrate_notes'] = deployment_substrates[self.deployment_media_dict[localization['media']]].get('Substrate Notes')
                localization_dict['deployment_notes'] = deployment_substrates[self.deployment_media_dict[localization['media']]].get('Deployment Notes')
            if scientific_name in self.phylogeny.keys():
                for key in self.phylogeny[scientific_name].keys():
                    # split to account for worms 'Phylum (Division)' case
                    localization_dict[key.split(' ')[0]] = self.phylogeny[scientific_name][key]
            formatted_localizations.append(localization_dict)

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
            'morphospecies',
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
            'deployment_notes',
            'phylum',
            'class',
            'subclass',
            'order',
            'suborder',
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

        def first_if_all_same(series):
            return series.iloc[0] if len(series.unique()) == 1 else f'Non-uniform values across dots: {series.unique()}'.replace("'", '"')

        localization_df = localization_df.groupby(['media_id', 'frame', 'scientific_name', 'tentative_id', 'type']).agg({
            'elemental_id': 'first',
            'timestamp': 'first',
            'camera_seafloor_arrival': 'first',
            'animal_arrival': 'first',
            'all_localizations': collect_localizations,
            'count': 'sum',
            'attracted': first_if_all_same,
            'categorical_abundance': first_if_all_same,
            'identification_remarks': first_if_all_same,
            'identified_by': first_if_all_same,
            'notes': first_if_all_same,
            'qualifier': first_if_all_same,
            'reason': first_if_all_same,
            'morphospecies': first_if_all_same,
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
            'deployment_notes': 'first',
            'phylum': 'first',
            'class': 'first',
            'subclass': 'first',
            'order': 'first',
            'suborder': 'first',
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
            'class',
            'subclass',
            'order',
            'suborder',
            'family',
            'subfamily',
            'genus',
            'species',
            'scientific_name',
            'tentative_id',
            'media_id',
            'frame',
        ])

        def is_populated(val):
            if isinstance(val, (list, pd.Series)):
                return pd.notnull(val).all()
            return pd.notnull(val)

        for index, row in localization_df.iterrows():
            record = {
                'observation_uuid': row['elemental_id'],
                'timestamp': row['timestamp'],
                'camera_seafloor_arrival': row['camera_seafloor_arrival'],
                'animal_arrival': row['animal_arrival'],
                'all_localizations': row['all_localizations'],
                'media_id': row['media_id'],
                'frame': row['frame'],
                'frame_url': row['frame_url'],
                'annotator': row['annotator'],
                'type': row['type'],
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
                'morphospecies': row['morphospecies'],
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
                'deployment_notes': row['deployment_notes'],
                'phylum': row['phylum'],
                'class': row['class'],
                'subclass': row['subclass'],
                'order': row['order'],
                'suborder': row['suborder'],
                'family': row['family'],
                'subfamily': row['subfamily'],
                'genus': row['genus'],
                'subgenus': row['subgenus'],
                'species': row['species'],
                'subspecies': row['subspecies'],
                'aphia_id': row['aphia_id'],
            }
            self.final_records.append({key: val for key, val in record.items() if is_populated(val)})
        self.save_phylogeny()
        print('processed!')
