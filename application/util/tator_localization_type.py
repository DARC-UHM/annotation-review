from enum import IntEnum


class TatorLocalizationType(IntEnum):
    BOX = 48
    DOT = 49
    SUB_BOX = 794
    SUB_DOT = 795

    @classmethod
    def is_relevant(cls, localization_type: int) -> bool:
        return localization_type in cls._value2member_map_

    @classmethod
    def is_box(cls, localization_type: int) -> bool:
        return localization_type == cls.BOX or localization_type == cls.SUB_BOX

    @classmethod
    def is_dot(cls, localization_type: int) -> bool:
        return localization_type == cls.DOT or localization_type == cls.SUB_DOT
