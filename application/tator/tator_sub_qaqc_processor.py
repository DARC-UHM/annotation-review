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
            if (not record.get('upon')
                    or record['upon'] in {'--', '-', ''}
                    or ('water' in record['upon'].lower() and record['phylum'] != 'Chordata')):
                record['problems'] = 'Upon'
                actual_final_records.append(record)
        self.final_records = actual_final_records

    def check_upons_are_current_substrate_or_previous_animal(self, transect_media: list[dict]):
        """
        Finds records where the "upon" attribute is not a substring of any value in the current substrate
        at the record's frame, and is not the scientific name of any animal previously recorded in the same
        media (skips upons with "water").
        """
        self.process_records()
        substrates = {
            substrate['media_id']: substrate['substrates']
            for substrate in
            self.tator_client.get_substrates_for_medias(project_id=self.project_id, transect_media=transect_media)
        }
        for media_id, substrate_entries in substrates.items():
            print(f'Substrates for media {media_id}:')
            for substrate in substrate_entries:
                print(f'  Frame {substrate["frame"]}: { {k: v for k, v in substrate.items() if k not in ("frame", "timestamp")} }')
        self.final_records.sort(key=lambda _record: (_record['media_id'], _record['frame']))
        actual_final_records = []
        seen_animals: dict[int, set] = {}  # media_id -> set of scientific names seen so far in that media
        for record in self.final_records:
            media_id = record['media_id']
            frame = record['frame']
            upon = record.get('upon')
            if upon and 'water' not in upon.lower():
                is_upon_in_current_substrate = self._upon_matches_substrate(upon, substrates.get(media_id, []), frame)
                is_upon_is_previous_animal = upon in seen_animals.get(media_id, set())
                if is_upon_is_previous_animal:
                    print(f'Matched upon "{upon}" for record at frame {frame} to previously seen animal')
                if not is_upon_in_current_substrate and not is_upon_is_previous_animal:
                    print(f'No match found for upon "{upon}" for record at frame {frame}')
                    record['problems'] = 'Upon'
                    record['substrate'] = self._get_substrate_for_frame(substrates.get(media_id, []), frame)
                    actual_final_records.append(record)
            seen_animals.setdefault(media_id, set()).add(record['scientific_name'])
        self.final_records = actual_final_records

    @staticmethod
    def _upon_matches_substrate(upon: str, substrate_entries: list[dict], frame: int) -> bool:
        """
        Returns True if upon is a substring of any substrate value in the current substrate state at the given frame.
        """
        invalid_values = {'--', '-', '', 'Not Set', 'None'}
        current_substrate = TatorSubQaqcProcessor._get_substrate_for_frame(substrate_entries, frame)
        if current_substrate is None:
            return False
        for key, val in current_substrate.items():
            if key in ('frame', 'timestamp'):
                continue
            if val not in invalid_values and upon.lower() in val.lower():
                print(f'Matched upon "{upon}" for record at frame {frame} to current {key} "{val}"')
                return True
        return False

    @staticmethod
    def _get_substrate_for_frame(substrate_entries: list[dict], frame: int) -> dict:
        """
        Returns the substrate state at the given frame, or None if there is no substrate state at or before that frame.
        """
        current_substrate = None
        for substrate in substrate_entries:
            if substrate['frame'] > frame:
                break
            current_substrate = substrate
        return current_substrate

    def get_suspicious_records(self):
        """
        Finds records where the "upon" attribute is suspicious, i.e. the same as the scientific name.
        """
        self.process_records()
        actual_final_records = []
        for record in self.final_records:
            if record['scientific_name'] == record.get('upon'):
                record['problems'] = 'Scientific Name,Upon'
                actual_final_records.append(record)
        self.final_records = actual_final_records

    def find_long_host_associate_time_diff(self):
        """
        Finds records where the "upon" attribute is an organism and there is either no previous record of that
        organism in the same media, or the closest previous record of that organism in the same media is more
        than one minute before the record.
        """
        self.process_records()
        media = self.tator_client.get_media_by_id(self.final_records[0]['media_id'])
        fps = media['fps']  # assume all media in a deployment are the same FPS
        actual_final_records = []
        self.final_records.sort(key=lambda _record: (_record['media_id'], _record['frame']))
        for i, record in enumerate(self.final_records):
            upon = record.get('upon')
            if not upon or 'Non-uniform values across dots' in upon:
                # check_missing_upon_and_not_fish handles missing upons
                # check_upons_are_current_substrate_or_previous_animal handles non-uniform dots
                continue
            if upon[0].isupper():  # expect substrates to be lowercase, scientific IDs to be capitalized
                most_recent_matching_host = None
                # start a lil ahead because we can have multiple localizations at the same timestamp
                j = min(i + 10, len(self.final_records) - 1)
                # make sure we're only looking at the current media_id and same timestamps
                while (j >= i and
                       (self.final_records[j]['media_id'] != record['media_id']
                        or self.final_records[j]['frame'] > record['frame'])):
                    j -= 1
                while j >= 0 and self.final_records[j]['media_id'] == record['media_id']:
                    if self.final_records[j]['scientific_name'] == upon:
                        most_recent_matching_host = self.final_records[j]
                        break
                    j -= 1
                if not most_recent_matching_host:
                    record['host_upon_time_diff'] = 'Unable to find matching host in previous records'
                    actual_final_records.append(record)
                    continue
                time_diff_seconds = int((record['frame'] - most_recent_matching_host['frame']) / fps)
                if time_diff_seconds > 60:
                    record['host_upon_time_diff'] = \
                        f'Most recent occurrence of "{upon}" more than 1 minute ago ({time_diff_seconds} seconds)'
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
