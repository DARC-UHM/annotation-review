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

    def process_records(self):
        concept_phylogeny = {'Animalia': {}, 'none': {}}
        annotation_df = pd.DataFrame(columns=[
            'observation_uuid',
            'concept',
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
            if concept_name not in concept_phylogeny.keys():
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
        for name in self.sequence_names:
            print(f'Fetching annotations for sequence {name} from VARS...', end='')

            with requests.get(f'http://hurlstor.soest.hawaii.edu:8086/query/dive/{name.replace(" ", "%20")}') as r:
                response = r.json()
                print('fetched!')

            for video in response['media']:
                if 'urn:imagecollection:org' not in video['uri']:
                    self.videos.append([
                        parse_datetime(video['start_timestamp']),
                        video['uri'].replace('http://hurlstor.soest.hawaii.edu/videoarchive', 'https://hurlvideo.soest.hawaii.edu'),
                        video['video_sequence_name']
                    ])

            for annotation in response['annotations']:
                # get list of associations
                association_set = set()
                duplicate_associations = []
                for association in annotation['associations']:
                    name = association['link_name']
                    if name not in association_set:
                        if name != 's2':
                            association_set.add(name)
                    else:
                        duplicate_associations.append(name)

                if duplicate_associations:
                    self.working_records.append(annotation)

        self.process_records()
