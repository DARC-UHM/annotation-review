from unittest.mock import patch

import pytest

from application.tator.tator_dropcam_qaqc_processor import TatorDropcamQaqcProcessor
from application.tator.tator_rest_client import TatorRestClient
from test.tator.conftest import TATOR_URL, make_localization, mock_get_section_by_id


@pytest.mark.usefixtures('mock_phylogeny_cache')
class TestTatorDropcamQaqcProcessor:
    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_check_attracted_not_attracted_flags_mismatches(self, fake_session, stub_annotator, stub_worms_match):
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        attracted_dict = {'Either': 2, 'NeverAttracted': 0, 'AlwaysAttracted': 1}
        tator_qaqc_processor.sections[0].localizations = [
            # scientific name not in attracted_dict at all -> flagged
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={
                    'Scientific Name': 'Not in dict',
                    'Attracted': 'Attracted',
                },
            ),
            # attracted_dict says "either" (2) -> always flagged
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={
                    'Scientific Name': 'Either',
                    'Attracted': 'Attracted',
                },
            ),
            # marked Attracted but attracted_dict says this taxon is never attracted (0) -> mismatch, flagged
            make_localization(
                elemental_id=3,
                frame=3,
                attributes={
                    'Scientific Name': 'NeverAttracted',
                    'Attracted': 'Attracted',
                },
            ),
            # marked Not Attracted but attracted_dict says this taxon is always attracted (1) -> mismatch, flagged
            make_localization(
                elemental_id=4,
                frame=4,
                attributes={
                    'Scientific Name': 'AlwaysAttracted',
                    'Attracted': 'Not Attracted',
                },
            ),
            # consistent with attracted_dict -> not flagged
            make_localization(
                elemental_id=5,
                frame=5,
                attributes={
                    'Scientific Name': 'AlwaysAttracted',
                    'Attracted': 'Attracted',
                },
            ),
            make_localization(
                elemental_id=6,
                frame=6,
                attributes={
                    'Scientific Name': 'NeverAttracted',
                    'Attracted': 'Not Attracted',
                },
            ),
        ]

        tator_qaqc_processor.check_attracted_not_attracted(attracted_dict)

        assert len(tator_qaqc_processor.final_records) == 4
        flagged_ids = {record['observation_uuid'] for record in tator_qaqc_processor.final_records}
        assert flagged_ids == {1, 2, 3, 4}

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_check_same_name_qualifier_flags_mismatched_qualifiers(
            self, fake_session, stub_annotator, stub_worms_match
    ):
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            # same scientific name, different qualifier -> both flagged
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={'Scientific Name': 'Mellivora', 'Qualifier': 'stet.'},
            ),
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={
                    'Scientific Name': 'Mellivora',
                    'Qualifier': 'indet.',
                },
            ),
            # same scientific name, same qualifier -> not flagged
            make_localization(
                elemental_id=3,
                frame=3,
                attributes={
                    'Scientific Name': 'Nautilus',
                    'Qualifier': 'stet.',
                },
            ),
            make_localization(
                elemental_id=4,
                frame=4,
                attributes={
                    'Scientific Name': 'Nautilus',
                    'Qualifier': 'stet.',
                },
            ),
            # same scientific name but different tentative ID -> treated as a different combo, not compared
            make_localization(
                elemental_id=5,
                frame=5,
                attributes={
                    'Scientific Name': 'Amphiprion',
                    'Tentative ID': 'Amphiprion barberi',
                    'Qualifier': 'stet.',
                },
            ),
            make_localization(
                elemental_id=6,
                frame=6,
                attributes={
                    'Scientific Name': 'Amphiprion',
                    'Tentative ID': 'Amphiprion ocellaris',
                    'Qualifier': 'indet.',
                },
            ),
        ]

        tator_qaqc_processor.check_same_name_qualifier()

        flagged_ids = {record['observation_uuid'] for record in tator_qaqc_processor.final_records}
        assert flagged_ids == {1, 2}

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_check_non_target_not_attracted_flags_attracted_non_target_records(
            self, fake_session, stub_annotator, stub_worms_match,
    ):
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            # non-target reason but still marked attracted -> flagged
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={
                    'Scientific Name': 'Oreamnos',
                    'Reason': 'Non-target taxon',
                    'Attracted': 'Attracted',
                },
            ),
            # non-target reason and correctly marked not attracted -> not flagged
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={
                    'Scientific Name': 'Cervidae',
                    'Reason': 'Non-target taxon',
                    'Attracted': 'Not Attracted',
                },
            ),
            # not a non-target reason at all -> not flagged
            make_localization(
                elemental_id=3,
                frame=3,
                attributes={
                    'Scientific Name': 'Carcharhinus',
                    'Reason': '--',
                    'Attracted': 'Attracted',
                },
            ),
        ]

        tator_qaqc_processor.check_non_target_not_attracted()

        assert len(tator_qaqc_processor.final_records) == 1
        assert tator_qaqc_processor.final_records[0]['observation_uuid'] == 1

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_check_exists_in_image_references(self, fake_session, stub_annotator, stub_worms_match):
        image_refs = {'Known': {}}
        tator_qaqc_processor = TatorDropcamQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            # plain scientific name already in image_refs -> not flagged
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={'Scientific Name': 'Known'},
            ),
            # plain scientific name not in image_refs -> flagged
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={'Scientific Name': 'Unknown'},
            ),
            # composite key (name + tentative ID) not in image_refs -> flagged
            make_localization(
                elemental_id=3,
                frame=3,
                attributes={'Scientific Name': 'Known', 'Tentative ID': 'Tent'},
            ),
            # both tentative ID and morphospecies set -> always flagged, regardless of image_refs
            make_localization(
                elemental_id=4,
                frame=4,
                attributes={'Scientific Name': 'Known', 'Tentative ID': 'Tent', 'Morphospecies': 'sp1'},
            ),
        ]

        tator_qaqc_processor.check_exists_in_image_references(image_refs)

        records_by_id = {record['observation_uuid']: record for record in tator_qaqc_processor.final_records}
        assert set(records_by_id.keys()) == {2, 3, 4}
        assert 'problems' not in records_by_id[2]
        assert 'problems' not in records_by_id[3]
        assert records_by_id[4]['problems'] == 'Tentative ID, Morphospecies'
