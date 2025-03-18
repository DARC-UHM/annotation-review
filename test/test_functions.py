import pytest

from application.util.functions import *
from test.data.vars_responses import ex_23060001
from test.data.worms_responses import clownfish_tree


class TestFunctions:
    def test_parse_datetime_micro(self):
        date_time = parse_datetime('2014-09-05T14:08:41.492Z')
        assert date_time == datetime(2014, 9, 5, 14, 8, 41, 492000)

    def test_parse_datetime_no_micro(self):
        date_time = parse_datetime('2014-09-05T14:08:41Z')
        assert date_time == datetime(2014, 9, 5, 14, 8, 41)

    def test_parse_datetime_fail(self):
        with pytest.raises(Exception):
            parse_datetime('fail')

    def test_extract_recorded_datetime_no_micro(self):
        date_time = extract_recorded_datetime(ex_23060001['annotations'][0])
        assert date_time == datetime(2023, 8, 24, 18, 36, 14)

    def test_extract_recorded_datetime_round_up(self):
        date_time = extract_recorded_datetime(ex_23060001['annotations'][1])
        assert date_time == datetime(2023, 8, 24, 21, 28, 26)

    def test_extract_recorded_datetime_round_down(self):
        date_time = extract_recorded_datetime(ex_23060001['annotations'][2])
        assert date_time == datetime(2014, 9, 20, 14, 13, 23)

    def test_extract_recorded_datetime_fail(self):
        assert extract_recorded_datetime({}) is None

    def test_get_association(self):
        test_obj = get_association(ex_23060001['annotations'][1], 'upon')
        assert test_obj == {
            'uuid': 'c4eaa100-upon',
            'link_name': 'upon',
            'to_concept': 'sed',
            'link_value': 'nil',
            'mime_type': 'text/plain'
        }

    def test_get_association_none(self):
        test_obj = get_association(ex_23060001['annotations'][0], 'test')
        assert test_obj == {}

    def test_format_annotator_normal(self):
        assert format_annotator(ex_23060001['annotations'][0]['observer']) == 'Nikki Cunanan'

    def test_format_annotator_harold(self):
        assert format_annotator('hcarlson') == 'Harold Carlson'

    def test_flatten_taxa_tree(self):
        assert flatten_taxa_tree(clownfish_tree, {}) == {
            'superdomain': 'Biota',
            'kingdom': 'Animalia',
            'phylum': 'Chordata',
            'subphylum': 'Vertebrata',
            'infraphylum': 'Gnathostomata',
            'parvphylum': 'Osteichthyes',
            'gigaclass': 'Actinopterygii',
            'superclass': 'Actinopteri',
            'class': 'Teleostei',
            'order': 'Ovalentaria incertae sedis',
            'family': 'Pomacentridae',
            'subfamily': 'Amphiprioninae',
        }
