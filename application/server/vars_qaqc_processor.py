import json
import os
import sys

import requests
import pandas as pd

from .functions import *

TERM_RED = '\033[1;31;48m'
TERM_NORMAL = '\033[1;37;0m'


class VarsQaqcProcessor:
    """
    Fetches annotation information from the VARS db on HURLSTOR given a list of sequences. Filters and formats the
    annotations for the various QA/QC checks.
    """

    def __init__(self, sequence_names: list):
        self.sequence_names = sequence_names
        self.videos = []
        self.working_records = []
        self.final_records = []

    def fetch_annotations(self, name):
        print(f'Fetching annotations for sequence {name} from VARS...', end='')
        sys.stdout.flush()

        with requests.get(f'http://hurlstor.soest.hawaii.edu:8086/query/dive/{name.replace(" ", "%20")}') as r:
            response = r.json()
            print('fetched!')

        for video in response['media']:
            if 'urn:imagecollection:org' not in video['uri']:
                self.videos.append([
                    parse_datetime(video['start_timestamp']),
                    video['uri'].replace('http://hurlstor.soest.hawaii.edu/videoarchive',
                                         'https://hurlvideo.soest.hawaii.edu'),
                    video['video_sequence_name']
                ])
        return response['annotations']

    def process_records(self):
        if not self.working_records:
            return
        formatted_annos = []

        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'r') as f:
                phylogeny = json.load(f)
        except FileNotFoundError:
            phylogeny = {'Animalia': {}}

        for annotation in self.working_records:
            concept_name = annotation['concept']
            if concept_name and concept_name not in phylogeny.keys():
                # get the phylogeny from VARS kb
                phylogeny[concept_name] = {}
                with requests.get(f'http://hurlstor.soest.hawaii.edu:8083/kb/v1/phylogeny/up/{concept_name}') \
                        as vars_tax_res:
                    if vars_tax_res.status_code == 200:
                        # this get us to phylum
                        try:
                            vars_tree = \
                                vars_tax_res.json()['children'][0]['children'][0]['children'][0]['children'][0]['children'][0]
                        except KeyError:
                            print(f'\n{TERM_RED}VARS phylogeny for {annotation["concept"]} not in expected format{TERM_NORMAL}')
                            vars_tree = {}
                        while 'children' in vars_tree.keys():
                            if 'rank' in vars_tree.keys():  # sometimes it's not
                                phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                            vars_tree = vars_tree['children'][0]
                        if 'rank' in vars_tree.keys():
                            phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                    else:
                        print(f'\n{TERM_RED}Unable to find record for {annotation["concept"]}{TERM_NORMAL}')

            # get image url
            image_url = None
            if annotation['image_references']:
                image_url = annotation['image_references'][0]['url']
                for i in range(1, len(annotation['image_references'])):
                    if '.png' in annotation['image_references'][i]['url']:
                        image_url = annotation['image_references'][i]['url']
                        break
                image_url = image_url.replace('http://hurlstor.soest.hawaii.edu/imagearchive',
                                              'https://hurlimage.soest.hawaii.edu')

            video_url = None
            video_sequence_name = None
            # get video reference url
            if 'recorded_timestamp' in annotation.keys():
                timestamp = parse_datetime(annotation['recorded_timestamp'])
                video_url = self.videos[0]
                for video in self.videos:
                    if video[0] > timestamp:
                        break
                    video_url = video
                time_diff = timestamp - video_url[0]
                video_sequence_name = video_url[2]
                video_url = f'{video_url[1]}#t={int(time_diff.total_seconds()) - 5}'

            formatted_annos.append({
                'observation_uuid': annotation['observation_uuid'],
                'concept': concept_name,
                'identity-reference': get_association(annotation, 'identity-reference')['link_value'] if get_association(annotation, 'identity-reference') else None,
                'associations': annotation['associations'],
                'image_url': image_url,
                'video_url': video_url,
                'recorded_timestamp': annotation['recorded_timestamp'],
                'video_sequence_name': video_sequence_name,
                'annotator': format_annotator(annotation['observer']),
                'activity': annotation['activity'] if 'activity' in annotation.keys() else None,
                'depth': int(annotation['ancillary_data']['depth_meters']) if 'ancillary_data' in annotation.keys() else None,
                'lat': round(annotation['ancillary_data']['latitude'], 3) if 'ancillary_data' in annotation.keys() else None,
                'long': round(annotation['ancillary_data']['longitude'], 3) if 'ancillary_data' in annotation.keys() else None,
                'phylum': phylogeny[concept_name]['phylum'] if 'phylum' in phylogeny[concept_name].keys() else None,
                'subphylum': phylogeny[concept_name]['subphylum'] if 'subphylum' in phylogeny[concept_name].keys() else None,
                'superclass': phylogeny[concept_name]['superclass'] if 'superclass' in phylogeny[concept_name].keys() else None,
                'class': phylogeny[concept_name]['class'] if 'class' in phylogeny[concept_name].keys() else None,
                'subclass': phylogeny[concept_name]['subclass'] if 'subclass' in phylogeny[concept_name].keys() else None,
                'superorder': phylogeny[concept_name]['superorder'] if 'superorder' in phylogeny[concept_name].keys() else None,
                'order': phylogeny[concept_name]['order'] if 'order' in phylogeny[concept_name].keys() else None,
                'suborder': phylogeny[concept_name]['suborder'] if 'suborder' in phylogeny[concept_name].keys() else None,
                'infraorder': phylogeny[concept_name]['infraorder'] if 'infraorder' in phylogeny[concept_name].keys() else None,
                'superfamily': phylogeny[concept_name]['superfamily'] if 'superfamily' in phylogeny[concept_name].keys() else None,
                'family': phylogeny[concept_name]['family'] if 'family' in phylogeny[concept_name].keys() else None,
                'subfamily': phylogeny[concept_name]['subfamily'] if 'subfamily' in phylogeny[concept_name].keys() else None,
                'genus': phylogeny[concept_name]['genus'] if 'genus' in phylogeny[concept_name].keys() else None,
                'species': phylogeny[concept_name]['species'] if 'species' in phylogeny[concept_name].keys() else None,
            })

        annotation_df = pd.DataFrame(formatted_annos)
        annotation_df = annotation_df.sort_values(by=[
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
            'concept',
            'recorded_timestamp',
        ])

        for index, row in annotation_df.iterrows():
            self.final_records.append({
                'observation_uuid': row['observation_uuid'],
                'concept': row['concept'],
                'identity_reference': row['identity-reference'],
                'annotator': row['annotator'],
                'activity': row['activity'],
                'depth': row['depth'],
                'lat': row['lat'],
                'long': row['long'],
                'phylum': row['phylum'],
                'class': row['class'],
                'order': row['order'],
                'infraorder': row['infraorder'],
                'family': row['family'],
                'genus': row['genus'],
                'species': row['species'],
                'image_url': row['image_url'],
                'video_url': row['video_url'],
                'recorded_timestamp': parse_datetime(row['recorded_timestamp']).strftime('%d %b %y %H:%M:%S UTC'),
                'video_sequence_name': row['video_sequence_name'],
                'associations': row['associations'],
            })

        try:
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(phylogeny, f, indent=2)
        except FileNotFoundError:
            os.makedirs('cache')
            with open(os.path.join('cache', 'phylogeny.json'), 'w') as f:
                json.dump(phylogeny, f, indent=2)

    def find_duplicate_associations(self):
        """
        Finds annotations that have more than one of the same association besides s2
        """
        for name in self.sequence_names:
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

    def find_missing_s1(self):
        """
        Finds annotations that are missing s1 (ignores 'none' records)
        """
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                if annotation['concept'] == 'none':
                    continue
                s1 = get_association(annotation, 's1')
                if not s1:
                    self.working_records.append(annotation)
        self.process_records()

    def find_identical_s1_s2(self):
        """
        Finds annotations that have an s2 association that is the same as its s1 association
        """
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                s2s = []
                s1 = ''
                for association in annotation['associations']:
                    if association['link_name'] == 's1':
                        s1 = association['to_concept']
                    elif association['link_name'] == 's2':
                        s2s.append(association['to_concept'])
                if s1 in s2s:
                    self.working_records.append(annotation)
        self.process_records()

    def find_duplicate_s2(self):
        """
        Finds annotations that have multiple s2 associations with the same value
        """
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                duplicate_s2s = False
                s2_set = set()
                for association in annotation['associations']:
                    if association['link_name'] == 's2':
                        if association['to_concept'] in s2_set:
                            duplicate_s2s = True
                            break
                        else:
                            s2_set.add(association['to_concept'])
                if duplicate_s2s:
                    self.working_records.append(annotation)
        self.process_records()

    def find_missing_upon_substrate(self):
        """
        Finds annotations that have an upon association that is not an organism, but the 'upon' is not present in s1 or
        any s2
        """
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                upon = None
                missing_upon = False
                for association in annotation['associations']:
                    if association['link_name'] == 'upon':
                        if association['to_concept'][0].isupper() or association['to_concept'].startswith('dead'):
                            # 'upon' is an organism, don't need it to be in s1/s2
                            pass
                        else:
                            # 'upon' should be in s1 or s2
                            upon = association['to_concept']
                        break
                if upon:
                    missing_upon = True
                    for association in annotation['associations']:
                        if (association['link_name'] == 's1' or association['link_name'] == 's2') \
                                and association['to_concept'] == upon:
                            missing_upon = False
                            break
                if missing_upon:
                    self.working_records.append(annotation)
        self.process_records()

    def find_mismatched_substrates(self):
        """
        Finds annotations that occur at the same timestamp (same second) but have different substrates
        """
        for name in self.sequence_names:
            annotations_with_same_timestamp = {}
            sorted_annotations = sorted(self.fetch_annotations(name), key=lambda d: d['recorded_timestamp'])
            # loop through all annotations, add ones with same timestamp to dict
            i = 0
            while i < len(sorted_annotations) - 1:
                base_timestamp = sorted_annotations[i]['recorded_timestamp'][:19]
                if sorted_annotations[i + 1]['recorded_timestamp'][:19] == base_timestamp:
                    indices_to_skip = 0
                    annotations_with_same_timestamp[base_timestamp] = [sorted_annotations[i]]
                    j = i + 1
                    while sorted_annotations[j]['recorded_timestamp'][:19] == base_timestamp:
                        annotations_with_same_timestamp[base_timestamp].append(sorted_annotations[j])
                        indices_to_skip += 1
                        j += 1
                    i += indices_to_skip
                i += 1
            # loop through each annotation that shares the same timestamp, compare substrates
            for timestamp_key in annotations_with_same_timestamp.keys():
                base_substrates = {'s2': set()}
                check_substrates = {'s2': set()}
                for association in annotations_with_same_timestamp[timestamp_key][0]['associations']:
                    if association['link_name'] == 's1':
                        base_substrates['s1'] = association['to_concept']
                    if association['link_name'] == 's2':
                        base_substrates['s2'].add(association['to_concept'])
                for i in range(1, len(annotations_with_same_timestamp[timestamp_key])):
                    for association in annotations_with_same_timestamp[timestamp_key][i]['associations']:
                        if association['link_name'] == 's1':
                            check_substrates['s1'] = association['to_concept']
                        if association['link_name'] == 's2':
                            check_substrates['s2'].add(association['to_concept'])
                if base_substrates != check_substrates:
                    for annotation in annotations_with_same_timestamp[timestamp_key]:
                        self.working_records.append(annotation)
        self.process_records()

    def find_missing_upon(self):
        """
        Finds annotations that are missing upon (ignores 'none' records)
        """
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                if annotation['concept'] == 'none':
                    continue
                if not get_association(annotation, 'upon'):
                    self.working_records.append(annotation)
        self.process_records()

    def get_num_records_missing_ancillary_data(self):
        """
        Finds number of annotations that are missing ancillary data
        """
        num_records_missing = 0
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                if 'ancillary_data' not in annotation.keys():
                    num_records_missing += 1
        return num_records_missing

    def find_missing_ancillary_data(self):
        """
        Finds annotations that are missing ancillary data (can be very slow)
        """
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                if 'ancillary_data' not in annotation.keys():
                    self.working_records.append(annotation)
        self.process_records()

    def find_id_refs_different_concept_name(self):
        """
        Finds annotations with the same ID reference that have different concept names
        """
        for name in self.sequence_names:
            id_ref_names = {}  # dict of {id_ref: {name_1, name_2}} to check for more than one name
            id_ref_annotations = {}  # dict of all annotations per id_ref: {id_ref: [annotation_1, annotation_2]}
            for annotation in self.fetch_annotations(name):
                for association in annotation['associations']:
                    if association['link_name'] == 'identity-reference':
                        if association['link_value'] not in id_ref_names.keys():
                            id_ref_names[association['link_value']] = set()
                            id_ref_annotations[association['link_value']] = []
                        id_ref_names[association['link_value']].add(annotation['concept'])
                        id_ref_annotations[association['link_value']].append(annotation)
                        break
            for id_ref, name_set in id_ref_names.items():
                if len(name_set) > 1:
                    for annotation in id_ref_annotations[id_ref]:
                        self.working_records.append(annotation)
        self.process_records()

    def find_id_refs_conflicting_associations(self):
        """
        Finds annotations with the same ID reference that have conflicting associations
        """
        to_concepts = ['s1', 's2', 'upon', 'size', 'guide-photo', 'habitat', 'megahabitat', 'sampled-by']
        for name in self.sequence_names:
            id_ref_associations = {}  # dict of {id_ref: {ass_1_name: ass_1_val, ass_2_name: ass_2_val}}
            id_ref_annotations = {}  # dict of all annotations per id_ref: {id_ref: [annotation_1, annotation_2]}
            for annotation in self.fetch_annotations(name):
                id_ref = get_association(annotation, 'identity-reference')
                if id_ref:
                    current_id_ref = id_ref['link_value']
                    if current_id_ref not in id_ref_associations.keys():
                        id_ref_associations[current_id_ref] = {
                            'flag': False,  # we'll set this to true if we find any conflicting associations
                            's2': set(),          # s2, sampled-by, and sample-reference are allowed to have
                            'sampled-by': set(),  # more than one association
                            'sample-reference': set(),
                        }
                        id_ref_annotations[current_id_ref] = []
                        id_ref_annotations[current_id_ref].append(annotation)
                        # populate id_ref dict with all associations
                        for ass in annotation['associations']:
                            if ass['link_name'] == 's2' or ass['link_name'] == 'sampled-by':
                                id_ref_associations[current_id_ref][ass['link_name']].add(ass['to_concept'])
                            elif ass['link_name'] == 'sample-reference':
                                id_ref_associations[current_id_ref][ass['link_name']].add(ass['link_value'])
                            else:
                                id_ref_associations[current_id_ref][ass['link_name']] = \
                                    ass['link_value'] if ass['link_name'] not in to_concepts else ass['to_concept']
                    else:
                        # check current association values vs those saved
                        id_ref_annotations[current_id_ref].append(annotation)
                        temp_s2_set = set()
                        temp_sampled_by_set = set()
                        temp_sample_ref_set = set()
                        for ass in annotation['associations']:
                            if ass['link_name'] == 's2':
                                temp_s2_set.add(ass['to_concept'])
                            elif ass['link_name'] == 'sampled-by':
                                temp_sampled_by_set.add(ass['to_concept'])
                            elif ass['link_name'] == 'sample-reference':
                                temp_sample_ref_set.add(ass['link_value'])
                            else:
                                if ass['link_name'] in to_concepts:
                                    if ass['link_name'] in id_ref_associations[current_id_ref].keys():
                                        # cases like 'guide-photo' will only be present on one record
                                        if id_ref_associations[current_id_ref][ass['link_name']] != ass['to_concept']:
                                            id_ref_associations[current_id_ref]['flag'] = True
                                            break
                                    else:
                                        id_ref_associations[current_id_ref][ass['link_name']] = ass['to_concept']
                                else:
                                    if ass['link_name'] in id_ref_associations[current_id_ref].keys():
                                        if id_ref_associations[current_id_ref][ass['link_name']] != ass['link_value']:
                                            id_ref_associations[current_id_ref]['flag'] = True
                                            break
                                    else:
                                        id_ref_associations[current_id_ref][ass['link_name']] = ass['link_value']
                        if temp_s2_set != id_ref_associations[current_id_ref]['s2'] \
                                or temp_sampled_by_set != id_ref_associations[current_id_ref]['sampled-by'] \
                                or temp_sample_ref_set != id_ref_associations[current_id_ref]['sample-reference']:
                            id_ref_associations[current_id_ref]['flag'] = True
                            break
                    break
            for id_ref in id_ref_associations.keys():
                if id_ref_associations[id_ref]['flag']:
                    for annotation in id_ref_annotations[id_ref]:
                        self.working_records.append(annotation)
        self.process_records()

    def find_suspicious_hosts(self):
        """
        Finds annotations that have an upon that is the same concept as itself
        """
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                upon = get_association(annotation, 'upon')
                if upon and upon['to_concept'] == annotation['concept']:
                    self.working_records.append(annotation)
        self.process_records()

    def find_missing_expected_association(self):
        """
        Finds annotations that are expected to be upon another organism, but are not. This is a very slow test because
        before it can begin, we must retrieve the taxa from VARS for every record (unlike the other tests, we can't
        filter beforehand).

        If more concepts need to be added for this check, simply add them to the appropriate list below:

            Example: To add the order 'order123' to the list, change the declaration below from:

            orders = ['Comatulida']

            to:

            orders = ['Comatulida', 'order123']

        If a list does not exist, declare a new list and add it to the conditional:

            Example: To add the subfamily 'subfam123' to the check, add a new list named 'subfamilies':

            subfamilies = ['subfam123']

            Then add the new list to the conditional:

            ...
            or ('family' in record.keys() and record['family'] in families)
            or ('subfamily' in record.keys() and record['subfamily'] in subfamilies)  <<< ADD THIS LINE
            or ('genus' in record.keys() and record['genus'] in genera)
            ...

        If you want the new addition to be highlighted in the table on the webpage, add the name to the ranksToHighlight
        list in qaqc.js, at ~line 340
        """
        classes = ['Ophiuroidea']
        orders = ['Comatulida']
        infraorders = ['Anomura', 'Caridea']
        families = ['Goniasteridae', 'Poecilasmatidae', 'Parazoanthidae', 'Tubulariidae', 'Amphianthidae', 'Actinoscyphiidae']
        genera = ['Henricia']
        concepts = ['Hydroidolina']
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                self.working_records.append(annotation)
        self.process_records()
        temp_records = self.final_records
        self.final_records = []
        for record in temp_records:
            if (
                    ('class' in record.keys() and record['class'] in classes)
                    or ('order' in record.keys() and record['order'] in orders)
                    or ('infraorder' in record.keys() and record['infraorder'] in infraorders)
                    or ('family' in record.keys() and record['family'] in families)
                    or ('genus' in record.keys() and record['genus'] in genera)
                    or ('concept' in record.keys() and record['concept'] in concepts)
            ):
                upon = get_association(record, 'upon')
                if upon and upon['to_concept'][0].islower():
                    self.final_records.append(record)

    def find_long_host_associate_time_diff(self):
        greater_than_one_min = {}
        greater_than_five_mins = {}
        not_found = []
        for name in self.sequence_names:
            sorted_annotations = sorted(self.fetch_annotations(name), key=lambda d: d['recorded_timestamp'])
            for i in range(len(sorted_annotations)):
                associate_record = sorted_annotations[i]
                upon = get_association(sorted_annotations[i], 'upon')
                if upon and upon['to_concept'][0].isupper():
                    # the associate's 'upon' is an organism
                    host_concept_name = upon['to_concept']
                    observation_time = extract_recorded_datetime(associate_record)
                    found = False
                    for j in range(i + 10, -1, -1):
                        """ 
                        Checks backward, looking for the most recent host w/ matching name. We start at i + 10 because 
                        there can be multiple records with the exact same timestamp, and one of those records could be 
                        the 'upon'
                        """
                        # to catch index out of range exception
                        while j >= len(sorted_annotations):
                            j -= 1
                        host_record = sorted_annotations[j]
                        host_time = extract_recorded_datetime(host_record)
                        if host_time > observation_time or i == j:
                            # host record won't be recorded after associate record, ignore this record
                            # i == j: record shouldn't be associated with itself, ignore
                            pass
                        else:
                            if host_record['concept'] == host_concept_name:
                                # the host record's name is equal to the host concept name (associate's 'upon' name)
                                found = True
                                time_diff = observation_time - host_time
                                if time_diff.seconds > 300:
                                    greater_than_five_mins[associate_record['observation_uuid']] = time_diff
                                    self.working_records.append(associate_record)
                                elif time_diff.seconds > 60:
                                    greater_than_one_min[associate_record['observation_uuid']] = time_diff
                                    self.working_records.append(associate_record)
                                break
                    if not found:
                        not_found.append(associate_record['observation_uuid'])
                        self.working_records.append(associate_record)
        self.process_records()
        for uuid in greater_than_one_min.keys():
            next((x for x in self.final_records if x['observation_uuid'] == uuid), None)['status'] = \
                'Time between record and closest previous matching host record greater than one minute ' \
                f'({greater_than_one_min[uuid].seconds} seconds)'
        for uuid in greater_than_five_mins.keys():
            next((x for x in self.final_records if x['observation_uuid'] == uuid), None)['status'] = \
                'Time between record and closest previous matching host record greater than five minutes ' \
                f'({greater_than_five_mins[uuid].seconds // 60 % 60} mins, {greater_than_five_mins[uuid].seconds % 60} seconds)'
        for uuid in not_found:
            next((x for x in self.final_records if x['observation_uuid'] == uuid), None)['status'] = \
                f'Host not found in previous records'

    def find_unique_fields(self):
        def load_dict(field_name, unique_dict, individual_count):
            if field_name not in unique_dict.keys():
                unique_dict[field_name] = {}
                unique_dict[field_name]['records'] = 1
                unique_dict[field_name]['individuals'] = individual_count
            else:
                unique_dict[field_name]['records'] += 1
                unique_dict[field_name]['individuals'] += individual_count

        unique_concept_names = {}
        unique_concept_upons = {}
        unique_substrate_combinations = {}
        unique_comments = {}
        unique_condition_comments = {}
        unique_megahabitats = {}
        unique_habitats = {}
        unique_habitat_comments = {}
        unique_id_certainty = {}
        unique_occurrence_remarks = {}

        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                substrates = []
                upon = None
                comment = None
                condition_comment = None
                megahabitat = None
                habitat = None
                habitat_comment = None
                id_certainty = None
                occurrence_remark = None
                individual_count = 1

                for association in annotation['associations']:
                    match association['link_name']:
                        case 's1' | 's2':
                            substrates.append(association['to_concept'])
                        case 'upon':
                            upon = association['to_concept']
                        case 'comment':
                            comment = association['link_value']
                        case 'condition-comment':
                            condition_comment = association['link_value']
                        case 'megahabitat':
                            megahabitat = association['to_concept']
                        case 'habitat':
                            habitat = association['to_concept']
                        case 'habitat-comment':
                            habitat_comment = association['link_value']
                        case 'identity-certainty':
                            id_certainty = association['link_value']
                        case 'occurrence-remark':
                            occurrence_remark = association['link_value']
                        case 'population-quantity':
                            individual_count = int(association['link_value'])
                        case 'categorical-abundance':
                            match association['link_value']:
                                case '11-20':
                                    individual_count = 15
                                case '21-50':
                                    individual_count = 35
                                case '51-100':
                                    individual_count = 75
                                case '\u003e100':
                                    individual_count = 100

                if substrates is not None:
                    substrates.sort()
                    substrates = ', '.join(substrates)

                load_dict(annotation['concept'], unique_concept_names, individual_count)
                load_dict(f'{annotation["concept"]}:{upon}', unique_concept_upons, individual_count)
                load_dict(substrates, unique_substrate_combinations, individual_count)
                load_dict(comment, unique_comments, individual_count)
                load_dict(condition_comment, unique_condition_comments, individual_count)
                load_dict(megahabitat, unique_megahabitats, individual_count)
                load_dict(habitat, unique_habitats, individual_count)
                load_dict(habitat_comment, unique_habitat_comments, individual_count)
                load_dict(id_certainty, unique_id_certainty, individual_count)
                load_dict(occurrence_remark, unique_occurrence_remarks, individual_count)

        self.final_records.append({'concept-names': unique_concept_names})
        self.final_records.append({'concept-upon-combinations': unique_concept_upons})
        self.final_records.append({'substrate-combinations': unique_substrate_combinations})
        self.final_records.append({'comments': unique_comments})
        self.final_records.append({'condition-comments': unique_condition_comments})
        self.final_records.append({'megahabitats': unique_megahabitats})
        self.final_records.append({'habitats': unique_habitats})
        self.final_records.append({'habitat-comments': unique_habitat_comments})
        self.final_records.append({'identity-certainty': unique_id_certainty})
        self.final_records.append({'occurrence-remarks': unique_occurrence_remarks})
