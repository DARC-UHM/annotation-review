import requests
import pandas as pd

from .functions import *


class QaqcProcessor:
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
        concept_phylogeny = {'Animalia': {}, 'none': {}, 'object': {}}
        annotation_df = pd.DataFrame(columns=[
            'observation_uuid',
            'concept',
            'identity-reference',
            'associations',
            'image_url',
            'video_url',
            'recorded_timestamp',
            'video_sequence_name',
            'annotator',
            'depth',
            'lat',
            'long',
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
            'species'
        ])

        for annotation in self.working_records:
            concept_name = annotation['concept']
            if concept_name and concept_name not in concept_phylogeny.keys():
                # get the phylogeny from VARS kb
                concept_phylogeny[concept_name] = {}
                with requests.get(f'http://hurlstor.soest.hawaii.edu:8083/kb/v1/phylogeny/up/{concept_name}') \
                        as vars_tax_res:
                    if vars_tax_res.status_code == 200:
                        # this get us to phylum
                        vars_tree = \
                            vars_tax_res.json()['children'][0]['children'][0]['children'][0]['children'][0]['children'][0]
                        while 'children' in vars_tree.keys():
                            if 'rank' in vars_tree.keys():  # sometimes it's not
                                concept_phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                            vars_tree = vars_tree['children'][0]
                        if 'rank' in vars_tree.keys():
                            concept_phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                    else:
                        print(f'\nUnable to find record for {annotation["concept"]}')

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

            temp_df = pd.DataFrame([[
                annotation['observation_uuid'],
                concept_name,
                get_association(annotation, 'identity-reference')['link_value'] if get_association(annotation, 'identity-reference') else None,
                annotation['associations'],
                image_url,
                video_url,
                annotation['recorded_timestamp'],
                video_sequence_name,
                format_annotator(annotation['observer']),
                int(annotation['ancillary_data']['depth_meters']) if 'ancillary_data' in annotation.keys() else None,
                round(annotation['ancillary_data']['latitude'], 3) if 'ancillary_data' in annotation.keys() else None,
                round(annotation['ancillary_data']['longitude'], 3) if 'ancillary_data' in annotation.keys() else None,
                concept_phylogeny[concept_name]['phylum'] if 'phylum' in concept_phylogeny[
                    concept_name].keys() else None,
                concept_phylogeny[concept_name]['subphylum'] if 'subphylum' in concept_phylogeny[
                    concept_name].keys() else None,
                concept_phylogeny[concept_name]['superclass'] if 'superclass' in concept_phylogeny[
                    concept_name].keys() else None,
                concept_phylogeny[concept_name]['class'] if 'class' in concept_phylogeny[
                    concept_name].keys() else None,
                concept_phylogeny[concept_name]['subclass'] if 'subclass' in concept_phylogeny[
                    concept_name].keys() else None,
                concept_phylogeny[concept_name]['superorder'] if 'superorder' in concept_phylogeny[
                    concept_name].keys() else None,
                concept_phylogeny[concept_name]['order'] if 'order' in concept_phylogeny[
                    concept_name].keys() else None,
                concept_phylogeny[concept_name]['suborder'] if 'suborder' in concept_phylogeny[
                    concept_name].keys() else None,
                concept_phylogeny[concept_name]['infraorder'] if 'infraorder' in concept_phylogeny[
                    concept_name].keys() else None,
                concept_phylogeny[concept_name]['superfamily'] if 'superfamily' in concept_phylogeny[
                    concept_name].keys() else None,
                concept_phylogeny[concept_name]['family'] if 'family' in concept_phylogeny[
                    concept_name].keys() else None,
                concept_phylogeny[concept_name]['subfamily'] if 'subfamily' in concept_phylogeny[
                    concept_name].keys() else None,
                concept_phylogeny[concept_name]['genus'] if 'genus' in concept_phylogeny[
                    concept_name].keys() else None,
                concept_phylogeny[concept_name]['species'] if 'species' in concept_phylogeny[
                    concept_name].keys() else None,
            ]], columns=[
                'observation_uuid',
                'concept',
                'identity-reference',
                'associations',
                'image_url',
                'video_url',
                'recorded_timestamp',
                'video_sequence_name',
                'annotator',
                'depth',
                'lat',
                'long',
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
                'species'
            ])

            annotation_df = pd.concat([annotation_df, temp_df], ignore_index=True)

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
            'recorded_timestamp'
        ])

        for index, row in annotation_df.iterrows():
            self.final_records.append({
                'observation_uuid': row['observation_uuid'],
                'concept': row['concept'],
                'identity_reference': row['identity-reference'],
                'annotator': row['annotator'],
                'depth': row['depth'],
                'lat': row['lat'],
                'long': row['long'],
                'phylum': row['phylum'],
                'class': row['class'],
                'order': row['order'],
                'family': row['family'],
                'genus': row['genus'],
                'species': row['species'],
                'image_url': row['image_url'],
                'video_url': row['video_url'],
                'recorded_timestamp': parse_datetime(row['recorded_timestamp']).strftime('%d %b %y %H:%M:%S UTC'),
                'video_sequence_name': row['video_sequence_name'],
                'associations': row['associations']
            })

    def find_duplicate_associations(self):
        """
        Finds annotations that have more than one of the same association besides s2
        """
        for name in self.sequence_names:
            annotations = self.fetch_annotations(name)
            for annotation in annotations:
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
            annotations = self.fetch_annotations(name)
            for annotation in annotations:
                if annotation['concept'] == 'none':
                    continue
                s1 = False
                for association in annotation['associations']:
                    if association['link_name'] == 's1':
                        s1 = True
                if not s1:
                    self.working_records.append(annotation)
        self.process_records()

    def find_identical_s1_s2(self):
        """
        Finds annotations that have an s2 association that is the same as its s1 association
        """
        for name in self.sequence_names:
            annotations = self.fetch_annotations(name)
            for annotation in annotations:
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
            annotations = self.fetch_annotations(name)
            for annotation in annotations:
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
        # TODO do we want to exclude dead organisms from this check?
        for name in self.sequence_names:
            annotations = self.fetch_annotations(name)
            for annotation in annotations:
                upon = None
                missing_upon = False
                for association in annotation['associations']:
                    if association['link_name'] == 'upon':
                        if association['to_concept'][0].isupper():
                            # 'upon' is an organism, don't need it to be in s1/s2
                            break
                        else:
                            # 'upon' should be in s1 or s2
                            upon = association['to_concept']
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
            annotations = self.fetch_annotations(name)
            annotations_with_same_timestamp = {}
            sorted_annotations = sorted(annotations, key=lambda d: d['recorded_timestamp'])
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
            annotations = self.fetch_annotations(name)
            for annotation in annotations:
                if annotation['concept'] == 'none':
                    continue
                missing_upon = True
                for association in annotation['associations']:
                    if association['link_name'] == 'upon':
                        missing_upon = False
                        break
                if missing_upon:
                    self.working_records.append(annotation)
        self.process_records()

    def get_num_records_missing_ancillary_data(self):
        """
        Finds number of annotations that are missing ancillary data
        """
        num_records_missing = 0
        for name in self.sequence_names:
            annotations = self.fetch_annotations(name)
            for annotation in annotations:
                if 'ancillary_data' not in annotation.keys():
                    num_records_missing += 1
        return num_records_missing

    def find_missing_ancillary_data(self):
        """
        Finds annotations that are missing ancillary data (can be very slow)
        """
        for name in self.sequence_names:
            annotations = self.fetch_annotations(name)
            for annotation in annotations:
                if 'ancillary_data' not in annotation.keys():
                    self.working_records.append(annotation)
        self.process_records()

    def find_id_refs_different_concept_name(self):
        """
        Finds annotations with the same ID reference that have different concept names
        """
        for name in self.sequence_names:
            annotations = self.fetch_annotations(name)
            id_ref_names = {}  # dict of {id_ref: {name_1, name_2}} to check for more than one name
            id_ref_annotations = {}  # dict of all annotations per id_ref: {id_ref: [annotation_1, annotation_2]}
            for annotation in annotations:
                for association in annotation['associations']:
                    if association['link_name'] == 'identity-reference':
                        if association['link_value'] not in id_ref_names.keys():
                            id_ref_names[association['link_value']] = set()
                            id_ref_annotations[association['link_value']] = []
                        id_ref_names[association['link_value']].add(annotation['concept'])
                        id_ref_annotations[association['link_value']].append(annotation)
                        break
            for id_ref, name_set in id_ref_names.items():
                print(f'{id_ref}: {name_set}')
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
            annotations = self.fetch_annotations(name)
            id_ref_associations = {}  # dict of {id_ref: {ass_1_name: ass_1_val, ass_2_name: ass_2_val}}
            id_ref_annotations = {}  # dict of all annotations per id_ref: {id_ref: [annotation_1, annotation_2]}
            for annotation in annotations:
                for association in annotation['associations']:
                    if association['link_name'] == 'identity-reference':
                        current_id_ref = association['link_value']
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
