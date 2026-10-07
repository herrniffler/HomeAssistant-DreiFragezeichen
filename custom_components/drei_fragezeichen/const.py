"""Constants for the Die drei ??? integration."""

from __future__ import annotations

DOMAIN = "drei_fragezeichen"
STORE_VERSION = 1

FORMATS = ("cd", "mc", "vinyl")
FORMAT_LABELS = {"cd": "CD", "mc": "MC", "vinyl": "Vinyl"}

SERIE_URL = "https://raw.githubusercontent.com/YourMJK/dreimetadaten/master/metadata/json/Serie.json"
ATTRIBUTION = "dreimetadaten.de (CC BY 4.0)"

REFRESH_INTERVAL_HOURS = 24

SERVICE_SET_OWNED = "set_owned"
ATTR_FORMAT = "format"
ATTR_OWNED = "owned"
ATTR_EPISODES = "episodes"
