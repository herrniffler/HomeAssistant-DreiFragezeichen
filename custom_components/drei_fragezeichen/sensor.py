"""Collection statistics."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTRIBUTION, FORMATS
from .controller import DreiFragezeichenConfigEntry, DreiFragezeichenController
from .entity import DreiFragezeichenEntity


@dataclass(frozen=True, kw_only=True)
class CollectionSensorDescription(SensorEntityDescription):
    value: Callable[[DreiFragezeichenController, list[int]], int]
    attributes: Callable[[DreiFragezeichenController, list[int]], dict[str, Any]] | None = None


def _owned_any(c: DreiFragezeichenController, released: list[int]) -> list[int]:
    return [n for n in released if c.owned.get(n)]


def _missing(c: DreiFragezeichenController, released: list[int]) -> list[int]:
    return [n for n in released if not c.owned.get(n)]


DESCRIPTIONS: tuple[CollectionSensorDescription, ...] = (
    CollectionSensorDescription(
        key="total",
        translation_key="total",
        icon="mdi:counter",
        value=lambda c, released: len(released),
    ),
    CollectionSensorDescription(
        key="owned",
        translation_key="owned",
        icon="mdi:check-circle-outline",
        value=lambda c, released: len(_owned_any(c, released)),
    ),
    CollectionSensorDescription(
        key="missing",
        translation_key="missing",
        icon="mdi:alert-circle-outline",
        value=lambda c, released: len(_missing(c, released)),
        attributes=lambda c, released: {"episodes": _missing(c, released)},
    ),
    *(
        CollectionSensorDescription(
            key=f"owned_{fmt}",
            translation_key=f"owned_{fmt}",
            value=lambda c, released, fmt=fmt: sum(
                1 for n in released if c.is_owned(n, fmt)
            ),
        )
        for fmt in FORMATS
    ),
    CollectionSensorDescription(
        key="latest",
        translation_key="latest",
        icon="mdi:new-box",
        value=lambda c, released: max(released, default=0),
        attributes=lambda c, released: (
            {
                "title": c.episodes[max(released)]["title"],
                "release_date": c.episodes[max(released)].get("date"),
            }
            if released
            else {}
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DreiFragezeichenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    controller = entry.runtime_data
    async_add_entities(CollectionSensor(controller, d) for d in DESCRIPTIONS)


class CollectionSensor(DreiFragezeichenEntity, SensorEntity):
    entity_description: CollectionSensorDescription
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        controller: DreiFragezeichenController,
        description: CollectionSensorDescription,
    ) -> None:
        super().__init__(controller, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> int:
        return self.entity_description.value(self.controller, self.controller.released)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attributes is None:
            return None
        return self.entity_description.attributes(
            self.controller, self.controller.released
        )
