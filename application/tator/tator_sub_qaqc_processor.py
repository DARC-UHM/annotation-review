import tator

from application.tator.tator_base_qaqc_processor import TatorBaseQaqcProcessor
from application.tator.tator_type import TatorLocalizationType


class TatorSubQaqcProcessor(TatorBaseQaqcProcessor):
    def __init__(
            self,
            project_id: int,
            section_ids: list[str],
            api: tator.api,
            tator_url: str,
            darc_review_url: str = None,
            transect_media_ids: list[int] = None,
    ):
        super().__init__(
            project_id=project_id,
            section_ids=section_ids,
            api=api,
            darc_review_url=darc_review_url,
            tator_url=tator_url,
            transect_media_ids=transect_media_ids,
        )

    def check_missing_ancillary_data(self):
        """
        Finds records that are missing ancillary data attributes:

        * "DO Temperature (celsius)" (do_temp_c)
        * "DO Concentration Salin Comp (mol per L)" (do_concentration_salin_comp_mol_L)
        * "Depth" (depth_m)
        """
        self.process_records()
        actual_final_records = []
        for record in self.final_records:
            if (not record.get('do_temp_c')
                    or not record.get('do_concentration_salin_comp_mol_L')
                    or not record.get('depth_m')):
                actual_final_records.append(record)
        self.final_records = actual_final_records

    def check_missing_upon_and_not_fish(self):
        """
        Finds records that are missing the "upon" attribute and are not a fish.
        """
        self.process_records()
        actual_final_records = []
        for record in self.final_records:
            if not record.get('upon') or ('water' in record['upon'].lower() and record['phylum'] != 'Chordata'):
                record['problems'] = 'Upon'
                actual_final_records.append(record)
        self.final_records = actual_final_records

    def get_unique_taxa(self):
        self.process_records()
        unique_taxa = {}
        for record in self.final_records:
            scientific_name = record.get('scientific_name')
            tentative_id = record.get('tentative_id', '')
            morphospecies = record.get('morphospecies', '')
            key = f'{scientific_name}:{tentative_id}:{morphospecies}'
            if key not in unique_taxa.keys():
                # add new unique taxa to dict
                unique_taxa[key] = {
                    'scientific_name': scientific_name,
                    'tentative_id': tentative_id,
                    'morphospecies': morphospecies,
                    'box_count': 0,
                    'dot_count': 0,
                }
            for localization in record['all_localizations']:
                # increment box/dot counts
                if TatorLocalizationType.is_box(localization['type']):
                    unique_taxa[key]['box_count'] += 1
                elif TatorLocalizationType.is_dot(localization['type']):
                    unique_taxa[key]['dot_count'] += 1
        self.final_records = unique_taxa

    def get_summary(self):
        raise NotImplementedError('TatorSubQaqcProcessor does not implement get_summary')

    def download_image_guide(self, app):
        raise NotImplementedError('TatorSubQaqcProcessor does not implement download_image_guide')
