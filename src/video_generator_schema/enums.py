from enum import Enum


class MouthShape(str, Enum):
    """6 mouth shapes mapped from VOICEVOX phonemes."""

    A = "a"
    I = "i"
    U = "u"
    E = "e"
    O = "o"
    CLOSED = "closed"


class Expression(str, Enum):
    """Zundamon facial expression presets."""

    NORMAL = "normal"
    SURPRISED = "surprised"
    TROUBLED = "troubled"


class Gender(str, Enum):
    """Reviewer gender."""

    MALE = "男性"
    FEMALE = "女性"
