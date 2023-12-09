import enum


class Site(enum.Enum):
    CHESSCOM = "chesscom"
    LICHESS = "lichess"


class Title(enum.Enum):
    GM = "GM"  # Grandmaster
    IM = "IM"  # International master
    FM = "FM"  # FIDE master
    CM = "CM"  # Candidate master
    NM = "NM"  # National master
    WGM = "WGM"
    WIM = "WIM"
    WFM = "WFM"
    WCM = "WCM"
    WNM = "WNM"
