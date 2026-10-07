"""Regenerate custom_components/drei_fragezeichen/episodes.json from dreimetadaten.

Usage: python tools/update_snapshot.py [path/to/Serie.json]
Without an argument the file is downloaded from GitHub.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPONENT = ROOT / "custom_components" / "drei_fragezeichen"
URL = "https://raw.githubusercontent.com/YourMJK/dreimetadaten/master/metadata/json/Serie.json"

spec = importlib.util.spec_from_file_location("episodes", COMPONENT / "episodes.py")
episodes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(episodes)


def main() -> None:
    if len(sys.argv) > 1:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        with urllib.request.urlopen(URL, timeout=60) as response:
            text = response.read().decode("utf-8")
    data = episodes.parse_episodes(text)
    out = {str(number): episode for number, episode in data.items()}
    target = COMPONENT / "episodes.json"
    target.write_text(
        json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    print(f"{len(out)} episodes -> {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
