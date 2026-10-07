"""Die drei ???: keep track of which main-series episodes you own on CD, MC and vinyl."""

from __future__ import annotations

import re

import voluptuous as vol

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_EPISODES,
    ATTR_FORMAT,
    ATTR_OWNED,
    DOMAIN,
    FORMATS,
    SERVICE_SET_OWNED,
    STORE_VERSION,
)
from .controller import DreiFragezeichenConfigEntry, DreiFragezeichenController

PLATFORMS = [Platform.SENSOR, Platform.SWITCH]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SET_OWNED_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_FORMAT): vol.In(FORMATS),
        vol.Required(ATTR_EPISODES): cv.string,
        vol.Optional(ATTR_OWNED, default=True): cv.boolean,
    }
)

_RANGE = re.compile(r"^(\d+)\s*-\s*(\d+)$")


def parse_episode_selection(text: str, available: list[int]) -> set[int]:
    """Parse "1-50, 52" or "all" into a set of episode numbers."""
    if text.strip().lower() in ("all", "alle"):
        return set(available)
    numbers: set[int] = set()
    for part in filter(None, (p.strip() for p in text.split(","))):
        if match := _RANGE.match(part):
            start, end = int(match[1]), int(match[2])
            if start > end:
                raise ServiceValidationError(f"Invalid range: {part}")
            numbers.update(range(start, end + 1))
        elif part.isdigit():
            numbers.add(int(part))
        else:
            raise ServiceValidationError(f"Cannot read episode selection: {part}")
    unknown = sorted(numbers - set(available))
    if unknown:
        raise ServiceValidationError(
            f"Unknown or unreleased episodes: {', '.join(map(str, unknown))}"
        )
    return numbers


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async def set_owned(call: ServiceCall) -> None:
        entries = hass.config_entries.async_loaded_entries(DOMAIN)
        if not entries:
            raise ServiceValidationError("Die drei ??? is not set up")
        controller = entries[0].runtime_data
        numbers = parse_episode_selection(call.data[ATTR_EPISODES], controller.released)
        controller.async_set_owned(numbers, call.data[ATTR_FORMAT], call.data[ATTR_OWNED])

    hass.services.async_register(
        DOMAIN, SERVICE_SET_OWNED, set_owned, schema=SET_OWNED_SCHEMA
    )
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: DreiFragezeichenConfigEntry
) -> bool:
    controller = DreiFragezeichenController(hass, entry)
    await controller.async_load()
    entry.runtime_data = controller

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    controller.async_start()
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: DreiFragezeichenConfigEntry
) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_flush()
    return unloaded


async def async_remove_entry(
    hass: HomeAssistant, entry: DreiFragezeichenConfigEntry
) -> None:
    await Store(hass, STORE_VERSION, f"{DOMAIN}.{entry.entry_id}").async_remove()
