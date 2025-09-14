"""Speisekammer Sensoren"""

from datetime import datetime, timedelta
import logging

from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import SpeisekammerAPI
from .const import CONF_COMMUNITY_ID

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Setup Sensoren für ConfigEntry."""
    token = entry.data.get("token")
    community_id = entry.data.get(CONF_COMMUNITY_ID)
    api = SpeisekammerAPI(token)

    sensors = [
        ExpiringItemsSensor(api, community_id),
        TotalItemsSensor(api, community_id),
        ItemsPerLocationSensor(api, community_id),
        ItemsPerLocationDetailsSensor(api, community_id),
    ]

    async_add_entities(sensors, update_before_add=True)


class ExpiringItemsSensor(Entity):
    """Sensor: Anzahl Artikel mit MHD in den nächsten X Tagen."""

    def __init__(self, api: SpeisekammerAPI, community_id: str, days_threshold: int = 3):
        self._api = api
        self._community_id = community_id
        self._days = days_threshold
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        return "Speisekammer Artikel bald ablaufend"

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def async_update(self):
        try:
            items = await self._api.get_items(self._community_id)
        except Exception as e:
            _LOGGER.error("Fehler beim Abrufen der Artikel: %s", e)
            self._state = 0
            self._attributes = {}
            return

        if not items:
            self._state = 0
            self._attributes = {}
            return

        now = datetime.utcnow()
        cutoff = now + timedelta(days=self._days)
        expiring = []

        for item in items:
            exp_date_str = item.get("expirationDate") or item.get("expiryDate")
            if not exp_date_str:
                continue
            try:
                exp_date = datetime.fromisoformat(exp_date_str)
            except ValueError:
                continue
            if now <= exp_date <= cutoff:
                expiring.append(item)

        self._state = len(expiring)
        self._attributes = {
            "items": [{"name": i.get("name"), "expires": i.get("expirationDate")} for i in expiring]
        }


class TotalItemsSensor(Entity):
    """Sensor: Gesamtanzahl Artikel."""

    def __init__(self, api: SpeisekammerAPI, community_id: str):
        self._api = api
        self._community_id = community_id
        self._state = None

    @property
    def name(self):
        return "Speisekammer Gesamtanzahl Artikel"

    @property
    def state(self):
        return self._state

    async def async_update(self):
        try:
            items = await self._api.get_items(self._community_id)
            self._state = len(items) if items else 0
        except Exception as e:
            _LOGGER.error("Fehler beim Abrufen der Artikel: %s", e)
            self._state = 0


class ItemsPerLocationSensor(Entity):
    """Sensor: Anzahl Artikel pro Lagerort."""

    def __init__(self, api: SpeisekammerAPI, community_id: str):
        self._api = api
        self._community_id = community_id
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        return "Speisekammer Artikel pro Lagerort"

    @property
    def state(self):
        return sum(self._attributes.values()) if self._attributes else 0

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def async_update(self):
        try:
            items = await self._api.get_items(self._community_id)
        except Exception as e:
            _LOGGER.error("Fehler beim Abrufen der Artikel: %s", e)
            self._state = 0
            self._attributes = {}
            return

        if not items:
            self._state = 0
            self._attributes = {}
            return

        locations = {}
        for item in items:
            loc = item.get("location", "Unbekannt")
            locations[loc] = locations.get(loc, 0) + 1

        self._attributes = locations
        self._state = sum(locations.values())


class ItemsPerLocationDetailsSensor(Entity):
    """Sensor: Detaillierte Auflistung pro Lagerort (für Markdown-Karte)."""

    def __init__(self, api: SpeisekammerAPI, community_id: str):
        self._api = api
        self._community_id = community_id
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        return "Speisekammer Artikel Details je Lagerort"

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def async_update(self):
        try:
            # Alle Lagerorte abfragen
            locations = await self._api.get_storage_locations(self._community_id)
            details = {}
            total_items = 0

            for loc in locations:
                loc_id = loc.get("id")
                loc_name = loc.get("name", "Unbekannt")
                items = await self._api.get_stock(self._community_id, loc_id)
                item_list = []

                for item in items:
                    name = item.get("name")
                    gtin = item.get("gtin")
                    for attr in item.get("attributes", []):
                        count = attr.get("count")
                        expiry = attr.get("bestBeforeDate")
                        item_list.append({
                            "name": name,
                            "gtin": gtin,
                            "count": count,
                            "expires": expiry
                        })
                        total_items += count

                details[loc_name] = item_list

            self._attributes = details
            self._state = total_items

        except Exception as e:
            _LOGGER.error("Fehler beim Abrufen der Lagerort-Details: %s", e)
            self._state = 0
            self._attributes = {}
