"""One switch per released episode and format: on = you own it."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import FORMAT_LABELS, FORMATS
from .controller import DreiFragezeichenConfigEntry, DreiFragezeichenController
from .entity import DreiFragezeichenEntity

ICONS = {"cd": "mdi:disc", "mc": "mdi:cassette", "vinyl": "mdi:album"}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DreiFragezeichenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    controller = entry.runtime_data
    async_add_entities(
        OwnedSwitch(controller, number, fmt)
        for number in controller.released
        for fmt in FORMATS
    )


class OwnedSwitch(DreiFragezeichenEntity, SwitchEntity):
    """Whether you own an episode on a given format."""

    def __init__(
        self, controller: DreiFragezeichenController, number: int, fmt: str
    ) -> None:
        super().__init__(controller, f"{number:03d}_{fmt}")
        self._number = number
        self._fmt = fmt
        episode = controller.episodes[number]
        self._attr_name = f"{number:03d} {episode['title']} ({FORMAT_LABELS[fmt]})"
        self._attr_icon = ICONS[fmt]

    @property
    def is_on(self) -> bool:
        return self.controller.is_owned(self._number, self._fmt)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        episode = self.controller.episodes[self._number]
        return {"number": self._number, "release_date": episode.get("date")}

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.controller.async_set_owned({self._number}, self._fmt, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.controller.async_set_owned({self._number}, self._fmt, False)
