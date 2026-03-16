from abc import abstractmethod, ABC

import sys
import tator

from pptx import Presentation

from application.tator.tator_localization_processor import TatorLocalizationProcessor


class TatorBaseQaqcProcessor(TatorLocalizationProcessor, ABC):
    """
    Fetches annotation information from the Tator given a project id, section id, and list of deployments.
    Filters and formats the annotations for the various QA/QC checks.
    """
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

    def check_names_accepted(self):
        """
        Finds records with a scientific name or tentative ID that is not accepted in WoRMS
        """
        print('Checking for accepted names...')
        sys.stdout.flush()
        checked = {}
        for section in self.sections:
            records_of_interest = []
            for localization in section.localizations:
                flag_record = False
                scientific_name = localization['attributes'].get('Scientific Name')
                tentative_id = localization['attributes'].get('Tentative ID')
                if scientific_name not in checked.keys():
                    if scientific_name in self.phylogeny.data:
                        checked[scientific_name] = True
                    else:
                        if self.phylogeny.fetch_worms(scientific_name):
                            checked[scientific_name] = True
                        else:
                            localization['problems'] = 'Scientific Name'
                            checked[scientific_name] = False
                            flag_record = True
                elif not checked[scientific_name]:
                    localization['problems'] = 'Scientific Name'
                    flag_record = True
                if tentative_id:
                    if tentative_id not in checked.keys():
                        if tentative_id in self.phylogeny.data:
                            checked[tentative_id] = True
                        else:
                            if self.phylogeny.fetch_worms(tentative_id):
                                checked[tentative_id] = True
                            else:
                                localization['problems'] = 'Tentative ID'
                                checked[tentative_id] = False
                                flag_record = True
                    elif not checked[tentative_id]:
                        localization['problems'] = 'Tentative ID' if 'problems' not in localization.keys() else 'Scientific Name, Tentative ID'
                        flag_record = True
                if flag_record:
                    records_of_interest.append(localization)
            print(f'Found {len(records_of_interest)} localizations with unaccepted names from {section.deployment_name}!')
            section.localizations = records_of_interest
        self.process_records(no_match_records={key for key in checked.keys() if not checked[key]})  # don't try to fetch again for names we already know are unaccepted

    def check_missing_qualifier(self):
        """
        Finds records that are classified higher than species but don't have a qualifier set (usually '--'). This check
        need to call process_records first to populate phylogeny.
        """
        self.process_records()
        actual_final_records = []
        for record in self.final_records:
            if not record.get('species') and record.get('qualifier', '--') == '--':
                record['problems'] = 'Scientific Name, Qualifier'
                actual_final_records.append(record)
        self.final_records = actual_final_records

    def check_stet_reason(self):
        """
        Finds records that have a qualifier of 'stet' but no reason set.
        """
        for section in self.sections:
            records_of_interest = []
            for localization in section.localizations:
                if localization['attributes'].get('Qualifier') == 'stet.' \
                        and localization['attributes'].get('Reason', '--') == '--':
                    localization['problems'] = 'Qualifier, Reason'
                    records_of_interest.append(localization)
            section.localizations = records_of_interest
        self.process_records()

    def get_all_tentative_ids_and_morphospecies(self):
        """
        Finds every record with a tentative ID or morphospecies. Also checks whether or not the tentative ID is in the same
        phylogenetic group as the scientific name.
        """
        no_match_records = set()
        records_of_interest = []
        for section in self.sections:
            for localization in section.localizations:
                tentative_id = localization['attributes'].get('Tentative ID')
                morphospecies = localization['attributes'].get('Morphospecies')
                is_record_of_interest = False
                localization_problems = ''
                if tentative_id and tentative_id not in ['--', '-', '']:
                    is_record_of_interest = True
                    localization_problems += 'Tentative ID'
                if morphospecies and morphospecies not in ['--', '-', '']:
                    is_record_of_interest = True
                    localization_problems += ' Morphospecies'
                if is_record_of_interest:
                    records_of_interest.append(localization)
                    localization['problems'] = localization_problems
            section.localizations = records_of_interest
        self.process_records()  # process first to make sure phylogeny is populated
        for localization in self.final_records:
            phylogeny_match = False
            if localization['tentative_id'] not in self.phylogeny.data:
                if localization['tentative_id'] not in no_match_records:
                    if not self.phylogeny.fetch_worms(localization['tentative_id']):
                        no_match_records.add(localization['tentative_id'])
                        localization['problems'] += ' phylogeny no match'
                        continue
                else:
                    localization['problems'] += ' phylogeny no match'
                    continue
            for value in self.phylogeny.data[localization['tentative_id']].values():
                if value == localization['scientific_name']:
                    phylogeny_match = True
                    break
            if not phylogeny_match:
                localization['problems'] += ' phylogeny no match'
        self.phylogeny.save()

    def get_all_notes_and_remarks(self):
        """
        Finds every record with a note or remark.
        """
        records_of_interest = []
        for section in self.sections:
            for localization in section.localizations:
                notes = localization['attributes'].get('Notes')
                id_remarks = localization['attributes'].get('IdentificationRemarks')
                has_note = notes and notes not in ['--', '-', '']
                has_remark = id_remarks and id_remarks not in ['--', '-', '']
                if has_note and has_remark:
                    localization['problems'] = 'Notes, ID Remarks'
                    records_of_interest.append(localization)
                elif has_note:
                    localization['problems'] = 'Notes'
                    records_of_interest.append(localization)
                elif has_remark:
                    localization['problems'] = 'ID Remarks'
                    records_of_interest.append(localization)
            section.localizations = records_of_interest
        self.process_records()

    def get_re_examined(self):
        """
        Finds all records that have a reason of "to be re-examined"
        """
        records_of_interest = []
        for section in self.sections:
            for localization in section.localizations:
                if localization['attributes'].get('Reason') == 'To be re-examined':
                    records_of_interest.append(localization)
            section.localizations = records_of_interest
        self.process_records()

    @abstractmethod
    def get_unique_taxa(self):
        """
        Finds every unique scientific name, tentative ID, and morphospecies combo and box/dot info.
        """
        pass

    @abstractmethod
    def get_summary(self):
        """
        Returns a summary of the final records.
        """
        pass

    @abstractmethod
    def download_image_guide(self, app) -> Presentation:
        """
        Finds all records marked as "good" images, saves them to a ppt.
        """
        pass
