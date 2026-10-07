"""Parser for the dreimetadaten main-series JSON (https://github.com/YourMJK/dreimetadaten).

Data licence: CC BY 4.0, attribution "dreimetadaten.de". Cover images and descriptions are
excluded from that licence, so they are dropped here and never stored.
"""

from __future__ import annotations

import json
from typing import Any


def _https(url: str | None) -> str | None:
    """The data lists http links, but the host also serves https (needed behind https HA)."""
    if url and url.startswith("http://"):
        return "https://" + url[len("http://") :]
    return url or None


def parse_episodes(serie_json: str) -> dict[int, dict[str, Any]]:
    """Return {number: {title, date, spotify, cover}} from Serie.json.

    "cover" is only the link to the image, the image itself is never downloaded.
    """
    episodes: dict[int, dict[str, Any]] = {}
    for item in json.loads(serie_json)["serie"]:
        episodes[int(item["nummer"])] = {
            "title": item["titel"],
            "date": item.get("veröffentlichungsdatum") or None,
            "spotify": (item.get("ids") or {}).get("spotify") or None,
            "cover": _https((item.get("links") or {}).get("cover")),
        }
    if not episodes:
        raise ValueError("no episodes found")
    return dict(sorted(episodes.items()))
