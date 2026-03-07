import json
import os

import requests

from application.util.constants import TERM_RED, TERM_YELLOW, TERM_NORMAL
from application.util.functions import flatten_taxa_tree

CACHE_PATH = os.path.join('cache', 'phylogeny.json')
WORMS_REST_URL = 'https://www.marinespecies.org/rest'


class PhylogenyCache:
    def __init__(self):
        self.data = {}
        self.load()

    def load(self):
        try:
            with open(CACHE_PATH, 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {'Animalia': {}}

    def save(self):
        try:
            with open(CACHE_PATH, 'w') as f:
                json.dump(self.data, f, indent=2)
        except FileNotFoundError:
            os.makedirs('cache')
            with open(CACHE_PATH, 'w') as f:
                json.dump(self.data, f, indent=2)

    def fetch_vars(self, concept_name: str, vars_kb_url: str, no_match_records: set):
        """
        Fetches phylogeny for a given concept from the VARS knowledge base.
        """
        print(f'Fetching phylogeny for "{concept_name}"')
        vars_tax_res = requests.get(url=f'{vars_kb_url}/phylogeny/up/{concept_name.replace("/", "%2F")}')
        if vars_tax_res.status_code == 200:
            try:
                # this gets us to phylum
                vars_tree = vars_tax_res.json()['children'][0]['children'][0]['children'][0]['children'][0]['children'][0]
                self.data[concept_name] = {}
            except KeyError:
                if concept_name not in no_match_records:
                    no_match_records.add(concept_name)
                    print(f'{TERM_YELLOW}WARNING: Could not find phylogeny for concept "{concept_name}" in VARS knowledge base{TERM_NORMAL}')
                vars_tree = {}
            while 'children' in vars_tree.keys():
                if 'rank' in vars_tree.keys():  # sometimes it's not
                    self.data[concept_name][vars_tree['rank']] = vars_tree['name']
                vars_tree = vars_tree['children'][0]
            if 'rank' in vars_tree.keys():
                self.data[concept_name][vars_tree['rank']] = vars_tree['name']
        else:
            print(f'\n{TERM_RED}Unable to find record for {concept_name}{TERM_NORMAL}')

    def fetch_worms(self, scientific_name: str) -> bool:
        """
        Fetches phylogeny for a given scientific name from WoRMS. Returns True if successful, False otherwise.
        """
        print(f'Fetching phylogeny for "{scientific_name}"')
        worms_id_res = requests.get(url=f'{WORMS_REST_URL}/AphiaIDByName/{scientific_name}?marine_only=true')
        if worms_id_res.status_code == 200 and worms_id_res.json() != -999:  # -999 means more than one matching record
            aphia_id = worms_id_res.json()
            worms_tree_res = requests.get(url=f'{WORMS_REST_URL}/AphiaClassificationByAphiaID/{aphia_id}')
            if worms_tree_res.status_code == 200:
                self.data[scientific_name] = flatten_taxa_tree(worms_tree_res.json(), {})
                self.data[scientific_name]['aphia_id'] = aphia_id
        else:
            worms_name_res = requests.get(url=f'{WORMS_REST_URL}/AphiaRecordsByName/{scientific_name}?like=false&marine_only=true&offset=1')
            if worms_name_res.status_code == 200 and len(worms_name_res.json()) > 0:
                # just take the first accepted record
                for record in worms_name_res.json():
                    if record['status'] == 'accepted':
                        worms_tree_res_2 = requests.get(url=f'{WORMS_REST_URL}/AphiaClassificationByAphiaID/{record["AphiaID"]}')
                        if worms_tree_res_2.status_code == 200:
                            self.data[scientific_name] = flatten_taxa_tree(worms_tree_res_2.json(), {})
                            self.data[scientific_name]['aphia_id'] = record['AphiaID']
                        break
            else:
                print(f'{TERM_RED}No accepted record found for concept name "{scientific_name}"{TERM_NORMAL}')
                return False
        return True
