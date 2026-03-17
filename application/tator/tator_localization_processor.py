import datetime
import os

import pandas as pd
import requests
import sys
import tator

from flask import session
from application.util.constants import TERM_RED, TERM_NORMAL
from application.tator.tator_type import TatorLocalizationType
from application.util.phylogeny_cache import PhylogenyCache
from application.tator.tator_rest_client import TatorRestClient


class Section:
    def __init__(self, section_id: str, api: tator.api):
        section_data = api.get_section(int(section_id))
        self.section_id = section_id
        self.deployment_name = section_data.name
        self.expedition_name = section_data.path.split('.')[0]
        self.localizations = []
        self.bottom_time = None


class TatorLocalizationProcessor:
    """
    Fetches all localization information for a given project/section/deployment list from Tator. Processes
    and sorts data for display on the image review pages.
    """

    BOTTOM_TIME_FORMAT = '%Y-%m-%d %H:%M:%SZ'

    def __init__(
        self,
        project_id: int,
        section_ids: list[str],
        api: tator.api,
        tator_url: str,
        darc_review_url: str = None,
        transect_media_ids: list[int] = None,
    ):
        self.project_id = project_id
        self.tator_url = tator_url
        self.darc_review_url = darc_review_url
        self.sections = [Section(section_id, api) for section_id in section_ids]
        self.api = api
        self.tator_client = TatorRestClient(tator_url, session['tator_token'])
        self.final_records: list[dict]|dict = []  # final list formatted for review page
        self.phylogeny = PhylogenyCache()
        self.transect_media_ids = set(media_id for media_id in transect_media_ids) if transect_media_ids else None

    def fetch_localizations(self):
        print('Fetching localizations...')
        sys.stdout.flush()
        if self.transect_media_ids:  # list of transects, fetch by media IDs instead of section
            section_map = {int(section.section_id): section for section in self.sections}
            media_id_list = list(self.transect_media_ids)
            for i in range(0, len(media_id_list), 50):
                batch = media_id_list[i:i + 50]
                for localization in self.tator_client.get_localizations(self.project_id, media_id=batch):
                    section = section_map.get(localization.get('master_section'), self.sections[0])
                    section.localizations.append(localization)
            for section in self.sections:
                print(f'Fetched {len(section.localizations)} localizations for deployment {section.deployment_name}')
        else:
            for section in self.sections:
                section.localizations = self.tator_client.get_localizations(self.project_id, section=section.section_id)
                print(f'Fetched {len(section.localizations)} localizations for deployment {section.deployment_name}')

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
        expedition_fieldbook = {}  # {section_id: deployments[]}
        media_substrates = {}  # {media_id: substrates}
        if 'media_fps' not in session:
            session['media_fps'] = {}

        if not no_match_records:
            no_match_records = set()

        for section in self.sections:
            for localization in section.localizations:
                if not TatorLocalizationType.is_relevant(localization['type']):
                    continue  # we only care about boxes and dots
                scientific_name = localization['attributes'].get('Scientific Name')
                cached_phylogeny = self.phylogeny.data.get(scientific_name)
                if (cached_phylogeny is None or 'aphia_id' not in cached_phylogeny.keys())\
                        and scientific_name not in no_match_records:
                    if not self.phylogeny.fetch_worms(scientific_name):
                        no_match_records.add(scientific_name)
                localization_dict = {
                    'elemental_id': localization['elemental_id'],
                    'section_id': section.section_id,
                    'all_localizations': {
                        'id': localization['id'],
                        'elemental_id': localization['elemental_id'],
                        'version': localization['version'],
                        'type': localization['type'],
                        'points': [round(localization['x'], 5), round(localization['y'], 5)],
                        'dimensions': [localization['width'], localization['height']] if TatorLocalizationType.is_box(localization['type']) else None,
                    },
                    'type': localization['type'],
                    'video_sequence_name': section.deployment_name,
                    'scientific_name': scientific_name,
                    'count': 0 if TatorLocalizationType.is_box(localization['type']) else 1,
                    'attracted': localization['attributes'].get('Attracted'),
                    'upon': localization['attributes'].get('Upon'),
                    'categorical_abundance': localization['attributes'].get('Categorical Abundance'),
                    'identification_remarks': localization['attributes'].get('IdentificationRemarks'),
                    'identified_by': localization['attributes'].get('Identified By'),
                    'notes': localization['attributes'].get('Notes'),
                    'qualifier': localization['attributes'].get('Qualifier'),
                    'reason': localization['attributes'].get('Reason'),
                    'morphospecies': localization['attributes'].get('Morphospecies'),
                    'tentative_id': localization['attributes'].get('Tentative ID'),
                    'good_image': True if localization['attributes'].get('Good Image') else False,
                    'annotator': self._get_annotator_name(localization['created_by']),
                    'frame': localization['frame'],
                    'frame_url': f'/tator/frame/{localization["media"]}/{localization["frame"]}',
                    'media_id': localization['media'],
                    'problems': localization['problems'] if 'problems' in localization.keys() else None,
                    'do_temp_c': localization['attributes'].get('DO Temperature (celsius)'),
                    'do_concentration_salin_comp_mol_L': localization['attributes'].get('DO Concentration Salin Comp (mol per L)'),
                    'depth_m': localization['attributes'].get('Depth'),
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
                    if section.bottom_time is None:
                        raise ValueError(f'No Arrival time found for section {section.deployment_name}. Cannot calculate timestamps.')
                    media_id = localization['media']
                    if media_id in session['media_timestamps'].keys():
                        if media_id not in session['media_fps'].keys():
                            session['media_fps'][media_id] = self.api.get_media(media_id).fps
                            session.modified = True
                        media_fps = session['media_fps'][media_id] or 30
                        camera_bottom_arrival = datetime.datetime.strptime(section.bottom_time, self.BOTTOM_TIME_FORMAT).replace(tzinfo=datetime.timezone.utc)
                        video_start_timestamp = datetime.datetime.fromisoformat(session['media_timestamps'][media_id]).astimezone(datetime.timezone.utc)
                        observation_timestamp = video_start_timestamp + datetime.timedelta(seconds=localization['frame'] / media_fps)
                        time_diff = observation_timestamp - camera_bottom_arrival
                        localization_dict['timestamp'] = observation_timestamp.strftime(self.BOTTOM_TIME_FORMAT)
                        localization_dict['camera_seafloor_arrival'] = camera_bottom_arrival.strftime(self.BOTTOM_TIME_FORMAT)
                        localization_dict['animal_arrival'] = str(datetime.timedelta(
                            days=time_diff.days,
                            seconds=time_diff.seconds
                        )) if observation_timestamp > camera_bottom_arrival else '00:00:00'
                if get_ctd:
                    if not expedition_fieldbook.get(section.section_id):
                        fieldbook_res = requests.get(
                            url=f'{self.darc_review_url}/dropcam-fieldbook/{section.section_id}',
                            headers={'API-Key': os.environ.get('DARC_REVIEW_API_KEY')},
                        )
                        if fieldbook_res.status_code == 200:
                            expedition_fieldbook[section.section_id] = fieldbook_res.json()['deployments']
                        else:
                            print(f'{TERM_RED}Error fetching expedition fieldbook.{TERM_NORMAL}')
                            print(fieldbook_res.text)
                    deployment_name = section.deployment_name.replace('-', '_')  # for DOEX0087_NIU-dscm-02
                    if section.section_id not in expedition_fieldbook.keys():
                        print(f'{TERM_RED}No fieldbook data found for section {section.section_id}{TERM_NORMAL}')
                        raise ValueError(f'No fieldbook data found for section {section.section_id}')
                    deployment_ctd = next((x for x in expedition_fieldbook[section.section_id] if x['deployment_name'] == deployment_name), None)
                    if deployment_ctd:
                        localization_dict['lat'] = deployment_ctd['lat']
                        localization_dict['long'] = deployment_ctd['long']
                        localization_dict['bait_type'] = deployment_ctd['bait_type']
                        localization_dict['depth_m'] = localization_dict['depth_m'] or deployment_ctd['depth_m']
                if get_substrates:
                    media_id = localization['media']
                    if not media_substrates.get(media_id):
                        media_substrates[media_id] = self.api.get_media(media_id).attributes
                    localization_dict['primary_substrate'] = media_substrates[media_id].get('Primary Substrate')
                    localization_dict['secondary_substrate'] = media_substrates[media_id].get('Secondary Substrate')
                    localization_dict['bedforms'] = media_substrates[media_id].get('Bedforms')
                    localization_dict['relief'] = media_substrates[media_id].get('Relief')
                    localization_dict['substrate_notes'] = media_substrates[media_id].get('Substrate Notes')
                    localization_dict['deployment_notes'] = media_substrates[media_id].get('Deployment Notes')
                if scientific_name in self.phylogeny.data:
                    for key in self.phylogeny.data[scientific_name].keys():
                        # split to account for worms 'Phylum (Division)' case
                        localization_dict[key.split(' ')[0]] = self.phylogeny.data[scientific_name][key]
                formatted_localizations.append(localization_dict)

        if not formatted_localizations:
            print('no records to process!')
            return

        localization_df = pd.DataFrame(formatted_localizations, columns=[
            'elemental_id',
            'section_id',
            'timestamp',
            'camera_seafloor_arrival',
            'animal_arrival',
            'all_localizations',
            'type',
            'video_sequence_name',
            'scientific_name',
            'count',
            'attracted',
            'upon',
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

        localization_df = localization_df.groupby([
            'media_id',
            'frame',
            'scientific_name',
            'tentative_id',
            'morphospecies',
            'type',
        ], dropna=False).agg({
            'elemental_id': 'first',
            'section_id': 'first',
            'timestamp': 'first',
            'camera_seafloor_arrival': 'first',
            'animal_arrival': 'first',
            'all_localizations': collect_localizations,
            'count': 'sum',
            'attracted': first_if_all_same,
            'upon': first_if_all_same,
            'categorical_abundance': first_if_all_same,
            'identification_remarks': first_if_all_same,
            'identified_by': first_if_all_same,
            'notes': first_if_all_same,
            'qualifier': first_if_all_same,
            'reason': first_if_all_same,
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
                'section_id': row['section_id'],
                'video_sequence_name': row['video_sequence_name'],
                'count': row['count'],
                'attracted': row['attracted'],
                'upon': row['upon'],
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
        self.phylogeny.save()
        print('processed!')

    def _get_annotator_name(self, user_id: int) -> str:
        if 'tator_usernames' not in session.keys():
            session['tator_usernames'] = {}
        if user_id not in session['tator_usernames']:
            print(f'Fetching annotator name for user ID {user_id} from Tator...')
            res_json = self.tator_client.get_user(user_id)
            if 'first_name' not in res_json:
                print(f'{TERM_RED}Error fetching annotator name for user ID {user_id}{TERM_NORMAL}')
                return f'Unknown annotator (#{user_id})'
            annotator_name = f'{res_json["first_name"]} {res_json["last_name"]}'
            print(f'Annotator name for user ID {user_id} is "{annotator_name}"')
            session['tator_usernames'][user_id] = annotator_name
            session.modified = True
        return session['tator_usernames'][user_id]
