import requests
import sys

from application.util.functions import *
from application.image_review.vars.vars_annotation_processor import VarsAnnotationProcessor


class VarsQaqcProcessor(VarsAnnotationProcessor):
    """
    Filters and formats annotations for the various DARC QA/QC checks.
    """

    def __init__(self, sequence_names: list, vars_dive_url: str, vars_phylogeny_url: str):
        super().__init__(sequence_names, vars_dive_url, vars_phylogeny_url)
        self.videos = []
        self.load_phylogeny()

    def fetch_annotations(self, seq_name):
        """
        Fetches annotations for a given sequence name from VARS
        """
        print(f'Fetching annotations for sequence {seq_name} from VARS...', end='')
        sys.stdout.flush()

        res = requests.get(url=f'{self.vars_dive_url}/{seq_name.replace(" ", "%20")}')
        dive_json = res.json()
        print('fetched!')

        for video in dive_json['media']:
            if 'urn:imagecollection:org' not in video['uri']:
                self.videos.append({
                    'start_timestamp': parse_datetime(video['start_timestamp']),
                    'uri': video['uri'].replace('http://hurlstor.soest.hawaii.edu/videoarchive', 'https://hurlvideo.soest.hawaii.edu'),
                    'sequence_name': video['video_sequence_name'],
                    'video_reference_uuid': video['video_reference_uuid'],
                })
        return dive_json['annotations']

    def find_duplicate_associations(self):
        """
        Finds annotations that have more than one of the same association besides s2
        """
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                if annotation.get('group') == 'localization':
                    continue
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
        self.sort_records(self.process_working_records(self.videos))

    def find_missing_s1(self):
        """
        Finds annotations that are missing s1 (ignores 'none' records)
        """
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                if annotation['concept'] == 'none' or annotation.get('group') == 'localization':
                    continue
                s1 = get_association(annotation, 's1')
                if not s1:
                    self.working_records.append(annotation)
        self.sort_records(self.process_working_records(self.videos))

    def find_identical_s1_s2(self):
        """
        Finds annotations that have an s2 association that is the same as its s1 association
        """
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                if annotation.get('group') == 'localization':
                    continue
                s2s = []
                s1 = ''
                for association in annotation['associations']:
                    if association['link_name'] == 's1':
                        s1 = association['to_concept']
                    elif association['link_name'] == 's2':
                        s2s.append(association['to_concept'])
                if s1 in s2s:
                    self.working_records.append(annotation)
        self.sort_records(self.process_working_records(self.videos))

    def find_duplicate_s2(self):
        """
        Finds annotations that have multiple s2 associations with the same value
        """
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                if annotation.get('group') == 'localization':
                    continue
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
        self.sort_records(self.process_working_records(self.videos))

    def find_missing_upon_substrate(self):
        """
        Finds annotations that have an upon association that is not an organism, but the 'upon' is not present in s1 or
        any s2
        """
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                if annotation.get('group') == 'localization':
                    continue
                upon = None
                missing_upon = False
                for association in annotation['associations']:
                    if association['link_name'] == 'upon':
                        if (association['to_concept'] and association['to_concept'][0].isupper()) \
                                or association['to_concept'].startswith('dead'):
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
        self.sort_records(self.process_working_records(self.videos))

    def find_mismatched_substrates(self):
        """
        Finds annotations that occur at the same timestamp (same second) but have different substrates
        """
        for name in self.sequence_names:
            annotations_with_same_timestamp = {}
            sorted_annotations = sorted(self.fetch_annotations(name), key=lambda d: d['recorded_timestamp'])
            # loop through all annotations, add ones with same timestamp to dict
            i = 0
            while i < len(sorted_annotations) - 2:
                if sorted_annotations[i].get('group') == 'localization':
                    i += 1
                    continue
                base_timestamp = sorted_annotations[i]['recorded_timestamp'][:19]
                base_annotation = sorted_annotations[i]
                i += 1
                while sorted_annotations[i]['recorded_timestamp'][:19] == base_timestamp:
                    if sorted_annotations[i].get('group') != 'localization':
                        if base_timestamp not in annotations_with_same_timestamp.keys():
                            annotations_with_same_timestamp[base_timestamp] = [base_annotation]
                        annotations_with_same_timestamp[base_timestamp].append(sorted_annotations[i])
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
        self.sort_records(self.process_working_records(self.videos))

    def find_missing_upon(self):
        """
        Finds annotations that are missing upon (ignores 'none' records)
        """
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                if annotation['concept'] == 'none' or annotation.get('group') == 'localization':
                    continue
                if not get_association(annotation, 'upon'):
                    self.working_records.append(annotation)
        self.sort_records(self.process_working_records(self.videos))

    def get_num_records_missing_ancillary_data(self):
        """
        Finds number of annotations that are missing ancillary data
        """
        num_records_missing = 0
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                if annotation.get('group') == 'localization':
                    continue
                if 'ancillary_data' not in annotation.keys():
                    num_records_missing += 1
        return num_records_missing

    def find_missing_ancillary_data(self):
        """
        Finds annotations that are missing ancillary data (can be very slow)
        """
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                if annotation.get('group') == 'localization':
                    continue
                if 'ancillary_data' not in annotation.keys():
                    self.working_records.append(annotation)
        self.sort_records(self.process_working_records(self.videos))

    def find_id_refs_different_concept_name(self):
        """
        Finds annotations with the same ID reference that have different concept names
        """
        for name in self.sequence_names:
            id_ref_names = {}  # dict of {id_ref: {name_1, name_2}} to check for more than one name
            id_ref_annotations = {}  # dict of all annotations per id_ref: {id_ref: [annotation_1, annotation_2]}
            for annotation in self.fetch_annotations(name):
                if annotation.get('group') == 'localization':
                    continue
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
        self.sort_records(self.process_working_records(self.videos))

    def find_id_refs_conflicting_associations(self):
        """
        Finds annotations with the same ID reference that have conflicting associations
        """
        to_concepts = ['s1', 's2', 'upon', 'size', 'habitat', 'megahabitat', 'sampled-by']
        for name in self.sequence_names:
            id_ref_associations = {}  # dict of {id_ref: {ass_1_name: ass_1_val, ass_2_name: ass_2_val}}
            id_ref_annotations = {}  # dict of all annotations per id_ref: {id_ref: [annotation_1, annotation_2]}
            for annotation in self.fetch_annotations(name):
                if annotation.get('group') == 'localization':
                    continue
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
                        id_ref_annotations[current_id_ref] = [annotation]
                        # populate id_ref dict with all associations
                        for ass in annotation['associations']:
                            if ass['link_name'] == 'guide-photo':
                                pass
                            elif ass['link_name'] == 's2' or ass['link_name'] == 'sampled-by':
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
                            if ass['link_name'] == 'guide-photo':
                                pass
                            elif ass['link_name'] == 's2':
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
            for id_ref in id_ref_associations.keys():
                if id_ref_associations[id_ref]['flag']:
                    for annotation in id_ref_annotations[id_ref]:
                        self.working_records.append(annotation)
        self.sort_records(self.process_working_records(self.videos))

    def find_blank_associations(self):
        """
        Finds all records that have associations with a link value of ""
        """
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                if annotation.get('group') == 'localization':
                    continue
                for association in annotation['associations']:
                    if association['link_value'] == "" and association['to_concept'] == 'self':
                        self.working_records.append(annotation)
        self.sort_records(self.process_working_records(self.videos))

    def find_suspicious_hosts(self):
        """
        Finds annotations that have an upon that is the same concept as itself
        """
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                if annotation.get('group') == 'localization':
                    continue
                upon = get_association(annotation, 'upon')
                if upon and upon['to_concept'] == annotation['concept']:
                    self.working_records.append(annotation)
        self.sort_records(self.process_working_records(self.videos))

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
        list in vars/qaqc.js, at ~line 340
        """
        classes = ['Ophiuroidea']
        orders = ['Comatulida']
        infraorders = ['Anomura', 'Caridea']
        families = ['Goniasteridae', 'Poecilasmatidae', 'Parazoanthidae', 'Tubulariidae', 'Amphianthidae', 'Actinoscyphiidae']
        genera = ['Henricia']
        concepts = ['Hydroidolina']
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                if annotation.get('group') == 'localization':
                    continue
                self.working_records.append(annotation)
        self.sort_records(self.process_working_records(self.videos))
        temp_records = self.final_records
        self.final_records = []
        for record in temp_records:
            if record.get('class') in classes \
                    or record.get('order') in orders \
                    or record.get('infraorder') in infraorders \
                    or record.get('family') in families \
                    or record.get('genus') in genera \
                    or record.get('concept') in concepts:
                upon = get_association(record, 'upon')
                if upon and upon['to_concept'][0].islower() and 'dead' not in upon['to_concept']:
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
                if upon and upon['to_concept'] and upon['to_concept'][0].isupper():
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
        self.sort_records(self.process_working_records(self.videos))
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

    def find_num_bounding_boxes(self):
        bounding_box_counts = {}
        total_count_annos = 0
        total_count_boxes = 0
        for name in self.sequence_names:
            for annotation in self.fetch_annotations(name):
                total_count_annos += 1
                if annotation['concept'] not in bounding_box_counts.keys():
                    bounding_box_counts[annotation['concept']] = {
                        'boxes': 0,
                        'annos': 0,
                    }
                bounding_box_counts[annotation['concept']]['annos'] += 1
                if get_association(annotation, 'bounding box'):
                    total_count_boxes += 1
                    bounding_box_counts[annotation['concept']]['boxes'] += 1
        sorted_box_counts = dict(sorted(bounding_box_counts.items()))
        self.final_records.append({
            'total_count_annos': total_count_annos,
            'total_count_boxes': total_count_boxes,
            'bounding_box_counts': sorted_box_counts,
        })

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
                            if association['link_value'] != '':
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
