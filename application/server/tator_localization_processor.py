import os
import json
import sys

import pandas as pd
import requests
import tator

from flask import session
from application.server.constants import KNOWN_ANNOTATORS
from application.server.functions import flatten_taxa_tree


class TatorLocalizationProcessor:
    """
    Fetches all localization information for a given project/section/deployment list from Tator. Processes
    and sorts data for display on the image review pages.
    """

    def __init__(self, project_id: int, section_id: int, api: tator.api, deployment_list: list):
        self.project_id = project_id
        self.section_id = section_id
        self.api = api
        self.deployments = deployment_list
        self.distilled_records = []
        self.section_name = self.api.get_section(self.section_id).name
        self.load_localizations()

    def load_localizations(self):
        print('Fetching localizations...', end='')
        sys.stdout.flush()
        media_ids = []
        deployment_media_dict = {}
        localizations = []

        for deployment in self.deployments:
            for media_id in session[f'{self.project_id}_{self.section_id}'][deployment]:
                deployment_media_dict[media_id] = deployment
            media_ids += session[f'{self.project_id}_{self.section_id}'][deployment]

        # REST is much faster than Python API for large queries
        # adding too many media ids results in a query that is too long, so we have to break it up
        for i in range(0, len(media_ids), 300):
            chunk = media_ids[i:i + 300]
            get_localization_res = requests.get(
                url=f'https://cloud.tator.io/rest/Localizations/{self.project_id}?media_id={",".join(map(str, chunk))}',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Token {session["tator_token"]}',
                })
            localizations += get_localization_res.json()
        print(f'fetched {len(localizations)} localizations!')
        print('Processing localizations...')
        sys.stdout.flush()

        formatted_localizations = []
        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'r') as f:
                phylogeny = json.load(f)
        except FileNotFoundError:
            phylogeny = {}

        for localization in localizations:
            if localization['type'] not in [48, 49]:  # we only care about boxes and dots
                continue
            scientific_name = localization['attributes']['Scientific Name']
            if scientific_name not in phylogeny.keys():
                worms_id_res = requests.get(f'https://www.marinespecies.org/rest/AphiaIDByName/{scientific_name}?marine_only=true')
                if worms_id_res.status_code == 200 and worms_id_res.json() != -999:  # -999 means more than one matching record
                    aphia_id = worms_id_res.json()
                    worms_tree_res = requests.get(f'https://www.marinespecies.org/rest/AphiaClassificationByAphiaID/{aphia_id}')
                    if worms_tree_res.status_code == 200:
                        phylogeny[scientific_name] = flatten_taxa_tree(worms_tree_res.json(), {})
                        phylogeny[scientific_name]['aphia_id'] = aphia_id
                else:
                    worms_name_res = requests.get(f'https://www.marinespecies.org/rest/AphiaRecordsByName/{scientific_name}?like=false&marine_only=true&offset=1')
                    if worms_name_res.status_code == 200 and len(worms_name_res.json()) > 0:
                        # just take the first accepted record
                        for record in worms_name_res.json():
                            if record['status'] == 'accepted':
                                worms_tree_res_2 = requests.get(f'https://www.marinespecies.org/rest/AphiaClassificationByAphiaID/{record["AphiaID"]}')
                                if worms_tree_res_2.status_code == 200:
                                    phylogeny[scientific_name] = flatten_taxa_tree(worms_tree_res_2.json(), {})
                                    phylogeny[scientific_name]['aphia_id'] = record['AphiaID']
                                break
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
                'video_sequence_name': deployment_media_dict[localization['media']],
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
                'good_image': True if localization['attributes'].get('Good Image') else False,
                'annotator': KNOWN_ANNOTATORS[localization['created_by']] if localization['created_by'] in KNOWN_ANNOTATORS.keys() else f'Unknown Annotator (#{localization["created_by"]})',
                'frame': localization['frame'],
                'frame_url': f'/tator/frame/{localization["media"]}/{localization["frame"]}',
                'media_id': localization['media'],
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
                        print(f'Unknown categorical abundance: {localization_dict["categorical_abundance"]}')
            if scientific_name in phylogeny.keys():
                for key in phylogeny[scientific_name].keys():
                    # split to account for worms 'Phylum (Division)' case
                    localization_dict[key.split(' ')[0]] = phylogeny[scientific_name][key]
            formatted_localizations.append(localization_dict)

        localization_df = pd.DataFrame(formatted_localizations, columns=[
            'elemental_id',
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
        ])

        def collect_localizations(items):
            return [item for item in items]

        localization_df = localization_df.groupby(['media_id', 'frame', 'scientific_name', 'type']).agg({
                'elemental_id': 'first',
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
                'good_image': 'first',
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
                'subgenus': 'first',
                'species': 'first',
                'subspecies': 'first',
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
            'tentative_id',
            'media_id',
            'frame',
        ])

        for index, row in localization_df.iterrows():
            self.distilled_records.append({
                'observation_uuid': row['elemental_id'],
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
                'phylum': row['phylum'],
                'class': row['class'],
                'order': row['order'],
                'family': row['family'],
                'genus': row['genus'],
                'subgenus': row['subgenus'],
                'species': row['species'],
                'subspecies': row['subspecies'],
            })

        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(phylogeny, f, indent=2)
        except FileNotFoundError:
            os.makedirs('cache')
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(phylogeny, f, indent=2)

        print('Processed!')
