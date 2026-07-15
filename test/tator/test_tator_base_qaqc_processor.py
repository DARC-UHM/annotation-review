from unittest.mock import call, patch

import pytest

from application.tator.tator_base_qaqc_processor import TatorBaseQaqcProcessor
from application.tator.tator_rest_client import TatorRestClient
from test.tator.conftest import TATOR_URL, make_localization, mock_get_section_by_id


class ConcreteQaqcProcessor(TatorBaseQaqcProcessor):
    def get_unique_taxa(self):
        pass

    def get_summary(self):
        pass


@pytest.mark.usefixtures('mock_phylogeny_cache')
class TestTatorBaseQaqcProcessor:
    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_check_names_accepted_flags_unmatched_scientific_name(self, fake_session, stub_annotator):
        def fake_fetch_worms(scientific_name):
            return scientific_name == 'Matched'

        tator_qaqc_processor = ConcreteQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.phylogeny.data['PreCached'] = {}  # data already present in the cache
        tator_qaqc_processor.sections[0].localizations = [
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={'Scientific Name': 'Matched'},
            ),
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={'Scientific Name': 'Unmatched'},
            ),
            # same unmatched name again -> should reuse the cached "known bad" result, not re-fetch (no_match_records)
            make_localization(
                elemental_id=3,
                frame=3,
                attributes={'Scientific Name': 'Unmatched'},
            ),
            make_localization(
                elemental_id=4,
                frame=4,
                attributes={'Scientific Name': 'PreCached'},
            ),
        ]

        with patch(
                'application.util.phylogeny_cache.PhylogenyCache.fetch_worms',
                side_effect=fake_fetch_worms,
        ) as mock_fetch_worms:
            tator_qaqc_processor.check_names_accepted()

        assert len(tator_qaqc_processor.final_records) == 2
        problems_by_id = {record['observation_uuid']: record['problems'] for record in tator_qaqc_processor.final_records}
        assert problems_by_id == {2: 'Scientific Name', 3: 'Scientific Name'}
        # the repeated 'Unmatched' should be fetched only once, thanks to check_names_accepted's own dedup
        assert mock_fetch_worms.call_args_list.count(call('Unmatched')) == 1

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_check_names_accepted_flags_unmatched_tentative_id(self, fake_session, stub_annotator):
        def fake_fetch_worms(scientific_name):
            return scientific_name != 'BadTentative'

        tator_qaqc_processor = ConcreteQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.phylogeny.data['PreCachedTentative'] = {}  # already resolved before this check runs
        tator_qaqc_processor.sections[0].localizations = [
            make_localization(
                localization_id=1,
                frame=1,
                attributes={
                    'Scientific Name': 'Good',
                    'Tentative ID': 'GoodTentative',
                },
            ),
            make_localization(
                localization_id=2,
                frame=2,
                attributes={
                    'Scientific Name': 'Good',
                    'Tentative ID': 'BadTentative',
                },
            ),
            # same unmatched tentative ID again -> should reuse the cached "known bad" result, not re-fetch
            make_localization(
                localization_id=3,
                frame=3,
                attributes={
                    'Scientific Name': 'Good',
                    'Tentative ID': 'BadTentative',
                },
            ),
            make_localization(
                localization_id=4,
                frame=4,
                attributes={
                    'Scientific Name': 'Good',
                    'Tentative ID': 'PreCachedTentative',
                },
            ),
        ]

        with patch(
                'application.util.phylogeny_cache.PhylogenyCache.fetch_worms',
                side_effect=fake_fetch_worms,
        ) as mock_fetch_worms:
            tator_qaqc_processor.check_names_accepted()

        assert len(tator_qaqc_processor.final_records) == 2
        problems_by_frame = {record['frame']: record['problems'] for record in tator_qaqc_processor.final_records}
        assert problems_by_frame == {2: 'Tentative ID', 3: 'Tentative ID'}
        assert mock_fetch_worms.call_args_list.count(call('BadTentative')) == 1

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    @pytest.mark.parametrize('has_species,qualifier,expected_flagged', [
        (True, '--', False),  # species-level ID with no qualifier: normal, not flagged
        (True, 'cf.', True),  # species-level ID but a qualifier is present: flagged
        (False, '--', True),  # higher-than-species ID with no qualifier explaining why: flagged
        (False, 'cf.', False),  # higher-than-species ID with a qualifier: normal, not flagged
    ])
    def test_check_missing_qualifier(self, fake_session, stub_annotator, has_species, qualifier, expected_flagged):
        def fake_fetch_worms(self, scientific_name):
            self.data[scientific_name] = {'species': scientific_name} if has_species else {'genus': scientific_name}
            return True

        tator_qaqc_processor = ConcreteQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            make_localization(
                attributes={
                    'Scientific Name': 'Name',
                    'Qualifier': qualifier,
                },
            ),
        ]

        with patch('application.util.phylogeny_cache.PhylogenyCache.fetch_worms', fake_fetch_worms):
            tator_qaqc_processor.check_missing_qualifier()

        if expected_flagged:
            assert len(tator_qaqc_processor.final_records) == 1
            assert tator_qaqc_processor.final_records[0]['problems'] == 'Scientific Name, Qualifier'
        else:
            assert len(tator_qaqc_processor.final_records) == 0

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_check_stet_reason_finds_records_missing_reason(self, fake_session, stub_annotator, stub_worms_match):
        tator_qaqc_processor = ConcreteQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            # 'stet.' with no Reason attribute (flagged)
            make_localization(
                localization_id=1,
                frame=1,
                attributes={
                    'Scientific Name': 'X',
                    'Qualifier': 'stet.',
                },
            ),
            # 'stet.' with a Reason given (not flagged)
            make_localization(
                localization_id=2,
                frame=2,
                attributes={
                    'Scientific Name': 'X',
                    'Qualifier': 'stet.',
                    'Reason': 'Non-target taxon',
                },
            ),
            # different qualifier entirely (not flagged)
            make_localization(
                localization_id=3,
                frame=3,
                attributes={
                    'Scientific Name': 'X',
                    'Qualifier': 'indet.',
                },
            ),
        ]

        tator_qaqc_processor.check_stet_reason()

        assert len(tator_qaqc_processor.final_records) == 1
        assert tator_qaqc_processor.final_records[0]['problems'] == 'Qualifier, Reason'

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_all_tentative_ids_and_morphospecies(self, fake_session, stub_annotator):
        def fake_fetch_worms(self, scientific_name):
            if scientific_name == 'Synaphobranchus':
                self.data['Synaphobranchus'] = {
                    'order': 'Anguilliformes',
                    'family': 'Synaphobranchidae',
                    'genus': 'Synaphobranchus',
                }
            elif scientific_name == 'Synaphobranchus affinis':
                self.data['Synaphobranchus affinis'] = {
                    'order': 'Anguilliformes',
                    'family': 'Synaphobranchidae',
                    'genus': 'Synaphobranchus',
                    'species': 'Synaphobranchus affinis',
                }
            elif scientific_name == 'Pseudocetonurus septifer':
                self.data['Pseudocetonurus septifer'] = {
                    'order': 'Gadiformes',
                    'family': 'Macrourinae',
                    'genus': 'Pseudocetonurus',
                    'species': 'Pseudocetonurus septifer',
                }
            return scientific_name in {'Synaphobranchus', 'Synaphobranchus affinis', 'Pseudocetonurus septifer'}

        tator_qaqc_processor = ConcreteQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            # tentative ID's phylogeny includes the observed scientific name as one of its ranks -> match
            # (but still flagged for having a tentative ID)
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={
                    'Scientific Name': 'Synaphobranchus',
                    'Tentative ID': 'Synaphobranchus affinis',
                },
            ),
            # tentative ID resolves via WoRMS but its phylogeny shares no rank with the scientific name -> flagged
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={
                    'Scientific Name': 'Synaphobranchus',
                    'Tentative ID': 'Pseudocetonurus septifer',
                },
            ),
            # tentative ID has no WoRMS match at all -> flagged
            make_localization(
                elemental_id=3,
                frame=3,
                attributes={
                    'Scientific Name': 'Synaphobranchus',
                    'Tentative ID': 'Unknown genus',
                },
            ),
            # same unmatched tentative ID again -> should reuse the cached "known no match" result, not re-fetch
            make_localization(
                elemental_id=4,
                frame=4,
                attributes={
                    'Scientific Name': 'Synaphobranchus',
                    'Tentative ID': 'Unknown genus',
                },
            ),
            # morphospecies set, no tentative ID -> still a record of interest
            make_localization(
                elemental_id=5,
                frame=5,
                attributes={
                    'Scientific Name': 'Synaphobranchus',
                    'Morphospecies': 'sp. 1',
                },
            ),
            # neither tentative ID nor morphospecies -> not a record of interest, excluded
            make_localization(
                elemental_id=6,
                frame=6,
                attributes={'Scientific Name': 'Synaphobranchus'},
            ),
        ]

        with patch('application.util.phylogeny_cache.PhylogenyCache.fetch_worms', fake_fetch_worms):
            tator_qaqc_processor.get_all_tentative_ids_and_morphospecies()

        assert len(tator_qaqc_processor.final_records) == 5
        records_by_id = {record['observation_uuid']: record for record in tator_qaqc_processor.final_records}
        assert records_by_id[1]['problems'] == 'Tentative ID'
        assert records_by_id[2]['problems'] == 'Tentative ID phylogeny no match'
        assert records_by_id[3]['problems'] == 'Tentative ID phylogeny no match'
        assert records_by_id[4]['problems'] == 'Tentative ID phylogeny no match'
        assert records_by_id[5]['problems'] == ' Morphospecies'

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_all_notes_and_remarks(self, fake_session, stub_annotator, stub_worms_match):
        tator_qaqc_processor = ConcreteQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={
                    'Scientific Name': 'X',
                    'Notes': 'has a note',
                },
            ),
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={
                    'Scientific Name': 'X',
                    'IdentificationRemarks': 'has a remark',
                },
            ),
            make_localization(
                elemental_id=3,
                frame=3,
                attributes={
                    'Scientific Name': 'X',
                    'Notes': 'a note',
                    'IdentificationRemarks': 'a remark',
                },
            ),
            # placeholder value, treated as "not set" -> excluded
            make_localization(
                elemental_id=4,
                frame=4,
                attributes={
                    'Scientific Name': 'X',
                    'Notes': '--',
                },
            ),
            # no notes/remarks
            make_localization(
                elemental_id=5,
                frame=5,
                attributes={'Scientific Name': 'X'},
            ),
        ]

        tator_qaqc_processor.get_all_notes_and_remarks()

        assert len(tator_qaqc_processor.final_records) == 3
        records_by_id = {record['observation_uuid']: record for record in tator_qaqc_processor.final_records}
        assert set(records_by_id.keys()) == {1, 2, 3}
        assert records_by_id[1]['problems'] == 'Notes'
        assert records_by_id[2]['problems'] == 'ID Remarks'
        assert records_by_id[3]['problems'] == 'Notes, ID Remarks'

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_get_re_examined(self, fake_session, stub_annotator, stub_worms_match):
        tator_qaqc_processor = ConcreteQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={
                    'Scientific Name': 'X',
                    'Reason': 'To be re-examined',
                },
            ),
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={
                    'Scientific Name': 'X',
                    'Reason': 'Non-target taxon',
                },
            ),
        ]

        tator_qaqc_processor.get_re_examined()

        assert len(tator_qaqc_processor.final_records) == 1
        assert tator_qaqc_processor.final_records[0]['observation_uuid'] == 1

    @patch.object(TatorRestClient, 'get_section_by_id', mock_get_section_by_id)
    def test_download_image_guide_filters_and_builds_presentation(self, fake_session, stub_annotator, stub_worms_match):
        tator_qaqc_processor = ConcreteQaqcProcessor(
            project_id=1,
            section_ids=['1'],
            tator_url=TATOR_URL,
        )
        tator_qaqc_processor.sections[0].localizations = [
            make_localization(
                elemental_id=1,
                frame=1,
                attributes={
                    'Scientific Name': 'X',
                    'Good Image': True,
                },
            ),
            make_localization(
                elemental_id=2,
                frame=2,
                attributes={
                    'Scientific Name': 'X',
                    'Good Image': False,
                },
            ),
            make_localization(
                elemental_id=3,
                frame=3,
                attributes={
                    'Scientific Name': 'X',
                    'Good Image': True,
                },
            ),
        ]

        with patch('application.tator.tator_base_qaqc_processor.ImageGuidePresentation') as mock_presentation_cls:
            mock_presentation_cls.return_value.build.return_value = 'a real cool presentation'
            result = tator_qaqc_processor.download_image_guide()

        assert len(tator_qaqc_processor.final_records) == 2
        assert tator_qaqc_processor.final_records[0]['observation_uuid'] == 1
        assert tator_qaqc_processor.final_records[1]['observation_uuid'] == 3
        mock_presentation_cls.return_value.build.assert_called_once_with(tator_qaqc_processor.final_records)
        assert result == 'a real cool presentation'
