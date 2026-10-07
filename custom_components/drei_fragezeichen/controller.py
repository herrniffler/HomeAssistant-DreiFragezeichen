"""Holds the episode list and which formats of each episode are owned."""

from __future__ import annotations

from datetime import date, timedelta
import json
import logging
from pathlib import Path
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN, FORMATS, REFRESH_INTERVAL_HOURS, SERIE_URL, STORE_VERSION
from .episodes import parse_episodes

_LOGGER = logging.getLogger(__name__)
SNAPSHOT = Path(__file__).parent / "episodes.json"
SAVE_DELAY = 1

DreiFragezeichenConfigEntry = ConfigEntry["DreiFragezeichenController"]


def _load_snapshot() -> dict[int, dict[str, Any]]:
    with SNAPSHOT.open(encoding="utf-8") as file:
        return {int(number): episode for number, episode in json.load(file).items()}


class DreiFragezeichenController:
    """Episode catalogue (from dreimetadaten.de) plus the user's collection."""

    def __init__(self, hass: HomeAssistant, entry: DreiFragezeichenConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.signal = f"{DOMAIN}_{entry.entry_id}_update"
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Die drei ???",
            manufacturer="dreimetadaten.de",
            model="Hauptreihe",
            entry_type=DeviceEntryType.SERVICE,
        )
        self._store: Store[dict[str, Any]] = Store(
            hass, STORE_VERSION, f"{DOMAIN}.{entry.entry_id}"
        )
        self.episodes: dict[int, dict[str, Any]] = {}
        self.owned: dict[int, set[str]] = {}

    async def async_load(self) -> None:
        stored = await self._store.async_load() or {}
        if stored.get("episodes"):
            self.episodes = {int(n): e for n, e in stored["episodes"].items()}
        else:
            self.episodes = await self.hass.async_add_executor_job(_load_snapshot)
        self.owned = {
            int(number): {f for f in formats if f in FORMATS}
            for number, formats in stored.get("owned", {}).items()
        }

    @callback
    def async_start(self) -> None:
        """Refresh the catalogue now (in the background) and then daily."""
        self.entry.async_create_background_task(
            self.hass, self.async_refresh(), f"{DOMAIN}_refresh"
        )
        self.entry.async_on_unload(
            async_track_time_interval(
                self.hass,
                self._async_scheduled_refresh,
                timedelta(hours=REFRESH_INTERVAL_HOURS),
            )
        )

    async def async_flush(self) -> None:
        await self._store.async_save(self._data())

    def _data(self) -> dict[str, Any]:
        return {
            "episodes": {str(n): e for n, e in self.episodes.items()},
            "owned": {str(n): sorted(f) for n, f in self.owned.items() if f},
        }

    @callback
    def _async_save_soon(self) -> None:
        self._store.async_delay_save(self._data, SAVE_DELAY)

    # --- catalogue ---------------------------------------------------------------

    @property
    def released(self) -> list[int]:
        """Episode numbers whose release date has been reached."""
        today = dt_util.now().date()
        return [n for n, e in self.episodes.items() if _is_released(e, today)]

    async def _async_scheduled_refresh(self, _now: Any) -> None:
        await self.async_refresh()

    async def async_refresh(self) -> None:
        """Fetch the main series from dreimetadaten.de; keep the cache on any failure."""
        before = self.released
        try:
            session = async_get_clientsession(self.hass)
            async with session.get(
                SERIE_URL, timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response.raise_for_status()
                text = await response.text(encoding="utf-8")
            episodes = await self.hass.async_add_executor_job(parse_episodes, text)
        except (aiohttp.ClientError, TimeoutError, ValueError, KeyError) as err:
            _LOGGER.warning("Could not refresh episodes from dreimetadaten.de: %s", err)
            episodes = self.episodes
        if episodes != self.episodes:
            self.episodes = episodes
            self._async_save_soon()
        if self.released != before:
            self.hass.config_entries.async_schedule_reload(self.entry.entry_id)
        else:
            self._async_signal()

    # --- collection --------------------------------------------------------------

    def is_owned(self, number: int, fmt: str) -> bool:
        return fmt in self.owned.get(number, ())

    @callback
    def async_set_owned(self, numbers: set[int], fmt: str, owned: bool) -> None:
        for number in numbers:
            formats = self.owned.setdefault(number, set())
            formats.add(fmt) if owned else formats.discard(fmt)
        self._async_save_soon()
        self._async_signal()

    @callback
    def _async_signal(self) -> None:
        async_dispatcher_send(self.hass, self.signal)


def _is_released(episode: dict[str, Any], today: date) -> bool:
    raw = episode.get("date")
    if not raw:
        return True
    try:
        return date.fromisoformat(raw) <= today
    except ValueError:
        return True
