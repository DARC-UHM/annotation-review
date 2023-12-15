import requests
import pandas as pd

from .functions import *

TERM_RED = '\033[1;31;48m'
TERM_NORMAL = '\033[1;37;0m'


class ImageProcessor:
    """
    Fetches annotation information from the VARS db on HURLSTOR given a list of sequences. Cleans, formats, and sorts
    the annotation data for display on the image review pages.
    """

    def __init__(self, sequence_names: list):
        self.distilled_records = []
        for name in sequence_names:
            self.load_images(name)

    def load_images(self, name: str):
        print(f'Fetching annotations for sequence {name} from VARS...', end='')
        concept_phylogeny = {'Animalia': {}}
        image_records = []
        videos = []

        with requests.get(f'http://hurlstor.soest.hawaii.edu:8086/query/dive/{name.replace(" ", "%20")}') as r:
            response = r.json()
            print('fetched!')
        print('Processing annotations...', end='')
        # get list of video links and start timestamps
        for video in response['media']:
            if 'urn:imagecollection:org' not in video['uri']:
                videos.append([parse_datetime(video['start_timestamp']),
                               video['uri'].replace('http://hurlstor.soest.hawaii.edu/videoarchive',
                                                    'https://hurlvideo.soest.hawaii.edu')])

        video_sequence_name = response['media'][0]['video_sequence_name']

        """ 
        Get all of the animal annotations that have images
        """
        for annotation in response['annotations']:
            concept_name = annotation['concept']
            if annotation['image_references'] and concept_name[0].isupper():
                image_records.append(annotation)
                if concept_name not in concept_phylogeny.keys():
                    # get the phylogeny from VARS kb
                    concept_phylogeny[concept_name] = {}
                    with requests.get(f'http://hurlstor.soest.hawaii.edu:8083/kb/v1/phylogeny/up/{concept_name}') \
                            as vars_tax_res:
                        if vars_tax_res.status_code == 200:
                            # this get us to phylum
                            try:
                                vars_tree = vars_tax_res.json()['children'][0]['children'][0]['children'][0]['children'][0]['children'][0]
                            except KeyError:
                                print(f'\n{TERM_RED}VARS phylogeny for {annotation["concept"]} not in expected format{TERM_NORMAL}')
                                vars_tree = {}
                            while 'children' in vars_tree.keys():
                                if 'rank' in vars_tree.keys():  # sometimes it's not
                                    concept_phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                                vars_tree = vars_tree['children'][0]
                            if 'rank' in vars_tree.keys():
                                concept_phylogeny[concept_name][vars_tree['rank']] = vars_tree['name']
                        else:
                            print(f'\n{TERM_RED}Unable to find record for {annotation["concept"]}{TERM_NORMAL}')

        """
        Define dataframe for sorting data
        """
        annotation_df = pd.DataFrame(columns=[
            'observation_uuid',
            'concept',
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

        # add the records to the dataframe, converts hyphens to underlines and remove excess data
        for record in image_records:
            concept_name = record['concept']

            # get image url
            image_url = record['image_references'][0]['url']
            for i in range(1, len(record['image_references'])):
                if '.png' in record['image_references'][i]['url']:
                    image_url = record['image_references'][i]['url']
                    break
            image_url = image_url.replace('http://hurlstor.soest.hawaii.edu/imagearchive',
                                          'https://hurlimage.soest.hawaii.edu')

            # get video reference url
            if 'recorded_timestamp' not in record.keys():
                break
            timestamp = parse_datetime(record['recorded_timestamp'])
            video_url = videos[0]
            for video in videos:
                if video[0] > timestamp:
                    break
                video_url = video
            time_diff = timestamp - video_url[0]
            video_url = f'{video_url[1]}#t={int(time_diff.total_seconds()) - 5}'

            temp_df = pd.DataFrame([[
                record['observation_uuid'],
                concept_name,
                get_association(record, 'identity-certainty')['link_value'] if get_association(record, 'identity-certainty') else None,
                get_association(record, 'identity-reference')['link_value'] if get_association(record, 'identity-reference') else None,
                get_association(record, 'guide-photo')['to_concept'] if get_association(record, 'guide-photo') else None,
                get_association(record, 'comment')['link_value'] if get_association(record, 'comment') else None,
                image_url,
                video_url,
                get_association(record, 'upon')['to_concept'] if get_association(record, 'upon') else None,
                record['recorded_timestamp'],
                video_sequence_name,
                format_annotator(record['observer']),
                int(record['ancillary_data']['depth_meters']) if 'ancillary_data' in record.keys() else None,
                round(record['ancillary_data']['latitude'], 3) if 'ancillary_data' in record.keys() else None,
                round(record['ancillary_data']['longitude'], 3) if 'ancillary_data' in record.keys() else None,
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
            'identity-reference',
            'identity-certainty',
            'recorded_timestamp'
        ])

        for index, row in annotation_df.iterrows():
            self.distilled_records.append({
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
        print('processed!')
