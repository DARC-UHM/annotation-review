import pandas as pd
import tator

from flask import session


class LocalizationProcessor:
    """
    Fetches all localization information for a given project/section from Tator. Processes and sorts data for display
    on the image review pages.
    """

    # TODO
    #  add ability to edit all clips in a deployment (FOV, substrate, location, etc)
    #  add external image review (download to server?)

    def __init__(self, project_id: int, section_id: int, api: tator.api):
        self.project_id = project_id
        self.section_id = section_id
        self.deployment_list = set()
        self.media_list = {}
        self.distilled_records = []
        self.api = api
        self.section_name = self.api.get_section(self.section_id).name
        self.load_media()
        self.load_localizations()

    def load_media(self):
        if f'{self.project_id}_{self.section_id}' in session.keys():
            self.media_list = session[f'{self.project_id}_{self.section_id}']['media_list']
            self.deployment_list = session[f'{self.project_id}_{self.section_id}']['deployment_list']
            print('Loaded media from session')
        else:
            print('Loading media...', end='')
            for media in self.api.get_media_list(project=self.project_id, section=self.section_id):
                self.media_list[media.id] = media.name
                self.deployment_list.add(media.name[:11])
            session[f'{self.project_id}_{self.section_id}'] = {
                'media_list': self.media_list,
                'deployment_list': self.deployment_list
            }
            session.modified = True
            print('done!')

    def load_localizations(self):
        print('Loading localizations...', end='')
        phylogeny = {'Animalia': {}}
        localizations = self.api.get_localization_list(
            project=self.project_id,
            section=self.section_id,
            start=0,
            stop=10,  # todo remove
        )

        """
        Define dataframe for sorting data
        """
        localization_df = pd.DataFrame(columns=[
            'id',
            'type',
            'points',
            'dimensions',
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
            'species',
        ])

        # add the records to the dataframe
        for localization in localizations:
            print(localization)
            scientific_name = localization.attributes['Scientific Name']
            if scientific_name not in phylogeny.keys():
                phylogeny[scientific_name] = {}
            temp_df = pd.DataFrame([[
                localization.id,
                localization.type,
                [localization.x, localization.y],
                [localization.width, localization.height] if localization.type == 48 else None,
                scientific_name,
                1,
                localization.attributes['Attracted'] if 'Attracted' in localization.attributes.keys() else None,
                localization.attributes['Categorical Abundance'] if 'Categorical Abundance' in localization.attributes.keys() else None,
                localization.attributes['IdentificationRemarks'] if 'IdentificationRemarks' in localization.attributes.keys() else None,
                localization.attributes['Identified By'] if 'Identified By' in localization.attributes.keys() else None,
                localization.attributes['Notes'] if 'Notes' in localization.attributes.keys() else None,
                localization.attributes['Qualifier'] if 'Qualifier' in localization.attributes.keys() else None,
                localization.attributes['Reason'] if 'Reason' in localization.attributes.keys() else None,
                localization.attributes['Tentative ID'] if 'Tentative ID' in localization.attributes.keys() else None,
                localization.created_by,
                localization.frame,
                f'/tator-frame/{localization.media}/{localization.frame}',
                localization.media,
                phylogeny[scientific_name]['phylum'] if 'phylum' in phylogeny[scientific_name].keys() else None,
                phylogeny[scientific_name]['subphylum'] if 'subphylum' in phylogeny[scientific_name].keys() else None,
                phylogeny[scientific_name]['superclass'] if 'superclass' in phylogeny[scientific_name].keys() else None,
                phylogeny[scientific_name]['class'] if 'class' in phylogeny[scientific_name].keys() else None,
                phylogeny[scientific_name]['subclass'] if 'subclass' in phylogeny[scientific_name].keys() else None,
                phylogeny[scientific_name]['superorder'] if 'superorder' in phylogeny[scientific_name].keys() else None,
                phylogeny[scientific_name]['order'] if 'order' in phylogeny[scientific_name].keys() else None,
                phylogeny[scientific_name]['suborder'] if 'suborder' in phylogeny[scientific_name].keys() else None,
                phylogeny[scientific_name]['infraorder'] if 'infraorder' in phylogeny[scientific_name].keys() else None,
                phylogeny[scientific_name]['superfamily'] if 'superfamily' in phylogeny[scientific_name].keys() else None,
                phylogeny[scientific_name]['family'] if 'family' in phylogeny[scientific_name].keys() else None,
                phylogeny[scientific_name]['subfamily'] if 'subfamily' in phylogeny[scientific_name].keys() else None,
                phylogeny[scientific_name]['genus'] if 'genus' in phylogeny[scientific_name].keys() else None,
                phylogeny[scientific_name]['species'] if 'species' in phylogeny[scientific_name].keys() else None,
            ]], columns=[
                'id',
                'type',
                'points',
                'dimensions',
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
                'species',
            ])

            localization_df = pd.concat([localization_df, temp_df], ignore_index=True)

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
        print('processed!')
