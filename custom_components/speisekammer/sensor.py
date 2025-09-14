"""Speisekammer Sensoren"""

from datetime import datetime, timedelta
from homeassistant.helpers.entity import Entity
from .api import SpeisekammerAPI
from .const import CONF_COMMUNITY_ID
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup Sensoren über Platform (wird von ConfigEntry aufgerufen)."""
    token = config.get("token")
    community_id = config.get(CONF_COMMUNITY_ID)
    api = SpeisekammerAPI(token)

    sensors = [
        ExpiringItemsSensor(api, community_id),
        TotalItemsSensor(api, community_id),
        ItemsPerLocationSensor(api, community_id),
        ItemsPerLocationDetailsSensor(api, community_id)
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
    """Sensor: Artikel pro Lagerort mit Details."""

    def __init__(self, api: SpeisekammerAPI, community_id: str):
        self._api = api
        self._community_id = community_id
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        return "Speisekammer Artikel pro Lagerort Details"

    @property
    def state(self):
        return sum([len(v) for v in self._attributes.values()]) if self._attributes else 0

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def async_update(self):
        try:
            # Alle Lagerorte abrufen
            storage_locations = await self._api.get_storage_locations(self._community_id)
            details = {}
            for loc in storage_locations:
                loc_id = loc["id"]
                loc_name = loc.get("name", loc_id)
                items = await self._api.get_stock(self._community_id, loc_id)
                details[loc_name] = [
                    {
                        "name": i["name"],
                        "gtin": i["gtin"],
                        "count": a["count"],
                        "bestBeforeDate": a.get("bestBeforeDate")
                    }
                    for i in items
                    for a in i.get("attributes", [])
                ]
            self._attributes = details
            self._state = sum([len(v) for v in details.values()])
        except Exception as e:
            _LOGGER.error("Fehler beim Abrufen der Artikel pro Lagerort Details: %s", e)
            self._state = 0
            self._attributes = {}
