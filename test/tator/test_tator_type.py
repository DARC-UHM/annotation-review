from application.tator.tator_type import TatorLocalizationType


class TestTatorLocalizationType:
    def test_is_box_or_dot_true_for_all_relevant_types(self):
        assert TatorLocalizationType.is_box_or_dot(TatorLocalizationType.BOX)
        assert TatorLocalizationType.is_box_or_dot(TatorLocalizationType.DOT)
        assert TatorLocalizationType.is_box_or_dot(TatorLocalizationType.SUB_BOX)
        assert TatorLocalizationType.is_box_or_dot(TatorLocalizationType.SUB_DOT)

    def test_is_box_or_dot_false_for_unrelated_type(self):
        assert not TatorLocalizationType.is_box_or_dot(999)

    def test_is_box(self):
        assert TatorLocalizationType.is_box(TatorLocalizationType.BOX)
        assert TatorLocalizationType.is_box(TatorLocalizationType.SUB_BOX)
        assert not TatorLocalizationType.is_box(TatorLocalizationType.DOT)
        assert not TatorLocalizationType.is_box(TatorLocalizationType.SUB_DOT)

    def test_is_dot(self):
        assert TatorLocalizationType.is_dot(TatorLocalizationType.DOT)
        assert TatorLocalizationType.is_dot(TatorLocalizationType.SUB_DOT)
        assert not TatorLocalizationType.is_dot(TatorLocalizationType.BOX)
        assert not TatorLocalizationType.is_dot(TatorLocalizationType.SUB_BOX)

    def test_is_dropcam(self):
        assert TatorLocalizationType.is_dropcam(TatorLocalizationType.BOX)
        assert TatorLocalizationType.is_dropcam(TatorLocalizationType.DOT)
        assert not TatorLocalizationType.is_dropcam(TatorLocalizationType.SUB_BOX)
        assert not TatorLocalizationType.is_dropcam(TatorLocalizationType.SUB_DOT)

    def test_is_sub(self):
        assert TatorLocalizationType.is_sub(TatorLocalizationType.SUB_BOX)
        assert TatorLocalizationType.is_sub(TatorLocalizationType.SUB_DOT)
        assert not TatorLocalizationType.is_sub(TatorLocalizationType.BOX)
        assert not TatorLocalizationType.is_sub(TatorLocalizationType.DOT)
