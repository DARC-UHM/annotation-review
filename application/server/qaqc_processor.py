import requests
import pandas as pd

from .functions import *


class QaqcProcessor:
    """
    Fetches annotation information from the VARS db on HURLSTOR given a list of sequences. Filters and formats the
    annotations for the various QA/QC checks.
    """

    def __init__(self, sequence_names: list):
        # set up dataframe for qaqc
        self.annotation_df = pd.DataFrame(columns=[
            'observation_uuid',
            'concept',
            'duplicate_associations',
            'identity-certainty',
            'identity-reference',
            'guide-photo',
            'comment',
            'image_url',
            'video_url',
            'upon',
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
        self.fetch_annotations(sequence_names)

    def fetch_annotations(self, sequence_names: list):
        concept_phylogeny = {'Animalia': {}, 'none': {}}
        for name in sequence_names:
            videos = []

            print(f'Fetching annotations for sequence {name} from VARS...', end='')

            with requests.get(f'http://hurlstor.soest.hawaii.edu:8086/query/dive/{name.replace(" ", "%20")}') as r:
                response = r.json()
                print('fetched!')

            # get list of video links and start timestamps
            for video in response['media']:
                if 'urn:imagecollection:org' not in video['uri']:
                    videos.append([parse_datetime(video['start_timestamp']),
                                   video['uri'].replace('http://hurlstor.soest.hawaii.edu/videoarchive',
                                                        'https://hurlvideo.soest.hawaii.edu')])

            video_sequence_name = response['media'][0]['video_sequence_name']

            for annotation in response['annotations']:
                concept_name = annotation['concept']
                if concept_name not in concept_phylogeny.keys() and name != 'none':
                    # get the phylogeny from VARS kb
                    concept_phylogeny[concept_name] = {}
                    with requests.get(f'http://hurlstor.soest.hawaii.edu:8083/kb/v1/phylogeny/up/{concept_name}') as vars_tax_res:
                        if vars_tax_res.status_code == 200:
                            # this get us to phylum
                            vars_tree = vars_tax_res.json()['children'][0]['children'][0]['children'][0]['children'][0]['children'][0]
                            while 'children' in vars_tree.keys():
                                if 'rank' in vars_tree.keys():  # sometimes it's not
                                    concept_phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                                vars_tree = vars_tree['children'][0]
                            if 'rank' in vars_tree.keys():
                                concept_phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                        else:
                            print(f'Unable to find record for {annotation["concept"]}')

                # check for image url
                image_url = None
                if annotation['image_references']:
                    image_url = annotation['image_references'][0]['url']
                    for i in range(1, len(annotation['image_references'])):
                        if '.png' in annotation['image_references'][i]['url']:
                            image_url = annotation['image_references'][i]['url']
                            break
                    image_url = image_url.replace('http://hurlstor.soest.hawaii.edu/imagearchive',
                                                  'https://hurlimage.soest.hawaii.edu')

                # get video reference url
                if 'recorded_timestamp' not in annotation.keys():
                    break
                timestamp = parse_datetime(annotation['recorded_timestamp'])
                video_url = videos[0]
                for video in videos:
                    if video[0] > timestamp:
                        break
                    video_url = video
                time_diff = timestamp - video_url[0]
                video_url = f'{video_url[1]}#t={int(time_diff.total_seconds()) - 5}'

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

                temp_df = pd.DataFrame([[
                    annotation['observation_uuid'],
                    concept_name,
                    duplicate_associations or None,
                    get_association(annotation, 'identity-certainty')['link_value'] if get_association(annotation, 'identity-certainty') else None,
                    get_association(annotation, 'identity-reference')['link_value'] if get_association(annotation, 'identity-reference') else None,
                    get_association(annotation, 'guide-photo')['to_concept'] if get_association(annotation, 'guide-photo') else None,
                    get_association(annotation, 'comment')['link_value'] if get_association(annotation, 'comment') else None,
                    image_url,
                    video_url,
                    get_association(annotation, 'upon')['to_concept'] if get_association(annotation, 'upon') else None,
                    annotation['recorded_timestamp'],
                    video_sequence_name,
                    format_annotator(annotation['observer']),
                    int(annotation['ancillary_data']['depth_meters']) if 'ancillary_data' in annotation.keys() else None,
                    round(annotation['ancillary_data']['latitude'], 3) if 'ancillary_data' in annotation.keys() else None,
                    round(annotation['ancillary_data']['longitude'], 3) if 'ancillary_data' in annotation.keys() else None,
                    concept_phylogeny[concept_name]['phylum'] if 'phylum' in concept_phylogeny[concept_name].keys() else None,
                    concept_phylogeny[concept_name]['subphylum'] if 'subphylum' in concept_phylogeny[concept_name].keys() else None,
                    concept_phylogeny[concept_name]['superclass'] if 'superclass' in concept_phylogeny[concept_name].keys() else None,
                    concept_phylogeny[concept_name]['class'] if 'class' in concept_phylogeny[concept_name].keys() else None,
                    concept_phylogeny[concept_name]['subclass'] if 'subclass' in concept_phylogeny[concept_name].keys() else None,
                    concept_phylogeny[concept_name]['superorder'] if 'superorder' in concept_phylogeny[concept_name].keys() else None,
                    concept_phylogeny[concept_name]['order'] if 'order' in concept_phylogeny[concept_name].keys() else None,
                    concept_phylogeny[concept_name]['suborder'] if 'suborder' in concept_phylogeny[concept_name].keys() else None,
                    concept_phylogeny[concept_name]['infraorder'] if 'infraorder' in concept_phylogeny[concept_name].keys() else None,
                    concept_phylogeny[concept_name]['superfamily'] if 'superfamily' in concept_phylogeny[concept_name].keys() else None,
                    concept_phylogeny[concept_name]['family'] if 'family' in concept_phylogeny[concept_name].keys() else None,
                    concept_phylogeny[concept_name]['subfamily'] if 'subfamily' in concept_phylogeny[concept_name].keys() else None,
                    concept_phylogeny[concept_name]['genus'] if 'genus' in concept_phylogeny[concept_name].keys() else None,
                    concept_phylogeny[concept_name]['species'] if 'species' in concept_phylogeny[concept_name].keys() else None,
                ]], columns=[
                    'observation_uuid',
                    'concept',
                    'duplicate_associations',
                    'identity-certainty',
                    'identity-reference',
                    'guide-photo',
                    'comment',
                    'image_url',
                    'video_url',
                    'upon',
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

                self.annotation_df = pd.concat([self.annotation_df, temp_df], ignore_index=True)

        self.annotation_df = self.annotation_df.sort_values(by=[
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
            'identity-reference',
            'identity-certainty',
            'recorded_timestamp'
        ])

    def duplicate_associations_check(self):
        df = self.annotation_df[pd.notna(self.annotation_df['duplicate_associations'])]
        records = []
        print(df.head())
        for index, row in df.iterrows():
            records.append({
                'observation_uuid': row['observation_uuid'],
                'concept': row['concept'],
                'duplicate_associations': row['duplicate_associations'],
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
                'identity_certainty': row['identity-certainty'],
                'identity_reference': row['identity-reference'],
                'guide_photo': row['guide-photo'],
                'comment': row['comment'],
                'image_url': row['image_url'],
                'video_url': row['video_url'],
                'upon': row['upon'],
                'recorded_timestamp': parse_datetime(row['recorded_timestamp']).strftime('%d %b %y %H:%M:%S UTC'),
                'video_sequence_name': row['video_sequence_name']
            })

        return records
