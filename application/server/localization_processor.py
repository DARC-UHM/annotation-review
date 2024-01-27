import os
import json
import pandas as pd
import requests
import tator

from typing import Dict
from flask import session


def flatten_taxa_tree(tree: Dict, flat: Dict):
    """
    Recursive function taking a taxonomy tree returned from WoRMS API and flattening it into a single dictionary.

    :param Dict tree: The nested taxon tree from WoRMS.
    :param Dict flat: The newly created flat taxon tree.
    """
    flat[tree['rank']] = tree['scientificname']
    if tree['child'] is not None:
        flatten_taxa_tree(tree['child'], flat)
    return flat


class LocalizationProcessor:
    """
    Fetches all localization information for a given project/section from Tator. Processes and sorts data for display
    on the image review pages.
    """

    # TODO
    #  add ability to edit all clips in a deployment (FOV, substrate, location, etc)
    #  add external image review (download to server?)

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
        phylogeny = {}
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
        print('Processing localizations...', end='')

        formatted_localizations = []
        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'r') as f:
                phylogeny = json.load(f)
        except FileNotFoundError:
            pass

        for localization in localizations:
            scientific_name = localization['attributes']['Scientific Name']
            if scientific_name not in phylogeny.keys():
                req = requests.get(f'https://www.marinespecies.org/rest/AphiaIDByName/{scientific_name}?marine_only=true')
                phylogeny[scientific_name] = {}
                if req.status_code == 200 and req.json() != -999:  # -999 means more than one matching record
                    aphia_id = req.json()
                    req = requests.get(f'https://www.marinespecies.org/rest/AphiaClassificationByAphiaID/{aphia_id}')
                    if req.status_code == 200:
                        phylogeny[scientific_name] = flatten_taxa_tree(req.json(), {})
                else:
                    req = requests.get(f'https://www.marinespecies.org/rest/AphiaRecordsByName/{scientific_name}?like=false&marine_only=true&offset=1')
                    if req.status_code == 200 and len(req.json()) > 0:
                        # just take the first accepted record
                        for record in req.json():
                            if record['status'] == 'accepted':
                                req = requests.get(f'https://www.marinespecies.org/rest/AphiaClassificationByAphiaID/{record["AphiaID"]}')
                                if req.status_code == 200:
                                    phylogeny[scientific_name] = flatten_taxa_tree(req.json(), {})
                                break
            formatted_localizations.append({
                'id': localization['id'],
                'type': localization['type'],
                'points': [localization['x'], localization['y']],
                'dimensions': [localization['width'], localization['height']] if localization['type'] == 48 else None,
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
                'annotator': localization['created_by'],
                'frame': localization['frame'],
                'frame_url': f'/tator-frame/{localization["media"]}/{localization["frame"]}',
                'media_id': localization['media'],
                'phylum': phylogeny[scientific_name]['Phylum'] if 'Phylum' in phylogeny[scientific_name].keys() else None,
                'subphylum': phylogeny[scientific_name]['Subphylum'] if 'Subphylum' in phylogeny[scientific_name].keys() else None,
                'superclass': phylogeny[scientific_name]['Superclass'] if 'Superclass' in phylogeny[scientific_name].keys() else None,
                'class': phylogeny[scientific_name]['Class'] if 'Class' in phylogeny[scientific_name].keys() else None,
                'subclass': phylogeny[scientific_name]['Subclass'] if 'Subclass' in phylogeny[scientific_name].keys() else None,
                'superorder': phylogeny[scientific_name]['Superorder'] if 'Superorder' in phylogeny[scientific_name].keys() else None,
                'order': phylogeny[scientific_name]['Order'] if 'Order' in phylogeny[scientific_name].keys() else None,
                'suborder': phylogeny[scientific_name]['Suborder'] if 'Suborder' in phylogeny[scientific_name].keys() else None,
                'infraorder': phylogeny[scientific_name]['Infraorder'] if 'Infraorder' in phylogeny[scientific_name].keys() else None,
                'superfamily': phylogeny[scientific_name]['Superfamily'] if 'Superfamily' in phylogeny[scientific_name].keys() else None,
                'family': phylogeny[scientific_name]['Family'] if 'Family' in phylogeny[scientific_name].keys() else None,
                'subfamily': phylogeny[scientific_name]['Subfamily'] if 'Subfamily' in phylogeny[scientific_name].keys() else None,
                'genus': phylogeny[scientific_name]['Genus'] if 'Genus' in phylogeny[scientific_name].keys() else None,
                'species': phylogeny[scientific_name]['Species'] if 'Species' in phylogeny[scientific_name].keys() else None,
            })

        localization_df = pd.DataFrame(formatted_localizations)

        def collect_points(points):
            return [point for point in points]

        localization_df = localization_df.groupby(['media_id', 'frame', 'scientific_name']).agg({
                'id': 'first',
                'type': 'first',
                'points': collect_points,
                'dimensions': 'first',
                'count': 'sum',
                'attracted': 'first',
                'categorical_abundance': 'first',
                'identification_remarks': 'first',
                'identified_by': 'first',
                'notes': 'first',
                'qualifier': 'first',
                'reason': 'first',
                'tentative_id': 'first',
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
                'id': row['id'],
                'type': row['type'],
                'media_id': row['media_id'],
                'frame': row['frame'],
                'frame_url': row['frame_url'],
                'annotator': row['annotator'],
                'points': row['points'],
                'dimensions': row['dimensions'],
                'scientific_name': row['scientific_name'],
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
