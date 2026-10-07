# Die drei ??? for Home Assistant

Keep track of which episodes of the main series you own on **CD**, **MC** (cassette) and **vinyl**.

## Installation
- HACS → Custom repository (Integration), or copy `custom_components/drei_fragezeichen` to `/config/custom_components/`
- Restart, then *Settings → Devices & services → Add integration → Die drei ???*

## What you get
One device "Die drei ???" with

- **Switches**: three per released episode, e.g. `switch.die_drei_001_und_der_super_papagei_cd`. On means you own it. That is about 735 entities, so use the search or a dashboard filter (see below).
- **Sensors**: *Episodes total*, *owned* (at least one format), *missing* (none; the numbers are in the `episodes` attribute), *on CD / MC / vinyl*, and *Latest episode*.
- **Service `drei_fragezeichen.set_owned`** to mark many at once, e.g. `format: cd`, `episodes: "1-50, 52, 60"` (or `all`), `owned: true`.

Each episode switch (and *Latest episode*) shows the cover as its entity picture, and the URL is in the `cover_url` attribute, e.g. for use in a picture-glance or markdown card. The link is taken from the dreimetadaten data (`links.cover`, e.g. `https://dreimetadaten.de/data/Serie/001/cover.png`); the integration never downloads or stores the images. They are 2-3 MB each and excluded from the CC BY licence of the data, so please do not show hundreds at once.

Your collection is stored in Home Assistant (`.storage/drei_fragezeichen.*`), nothing is sent anywhere.

Only the main series is covered. Episodes show up as soon as their release date is reached.

### Dashboard tip
With the [auto-entities](https://github.com/thomasloven/lovelace-auto-entities) card from HACS you can list only what is missing on CD:

```yaml
type: custom:auto-entities
card:
  type: entities
  title: Missing on CD
filter:
  include:
    - entity_id: "switch.die_drei_*_cd"
      state: "off"
sort:
  method: entity_id
```

## Data source and licence
The episode list (number, title, release date) is loaded daily from
[dreimetadaten](https://github.com/YourMJK/dreimetadaten) (`metadata/json/Serie.json`) and cached;
a snapshot ships with the integration so it also works offline. Cover images and descriptions are
not used or stored.

Data: **dreimetadaten.de**, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Integration code: MIT (see `LICENSE`).

To refresh the bundled snapshot: `python tools/update_snapshot.py`.
