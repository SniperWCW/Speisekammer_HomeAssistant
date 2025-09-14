"""Speisekammer Sensoren"""

from datetime import datetime, timedelta
from homeassistant.helpers.entity import Entity
from .api import SpeisekammerAPI
from .const import CONF_COMMUNITY_ID
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup der Sensoren über Platform (aufgerufen von ConfigEntry)."""
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
            for attr in item.get("attributes", []):
                exp_date_str = attr.get("bestBeforeDate")
                if not exp_date_str:
                    continue
                try:
                    exp_date = datetime.fromisoformat(exp_date_str.replace("Z", "+00:00"))
                except ValueError:
                    continue
                if now <= exp_date <= cutoff:
                    expiring.append({
                        "name": item.get("name"),
                        "expires": exp_date_str,
                        "count": attr.get("count"),
                        "gtin": item.get("gtin")
                    })

        self._state = len(expiring)
        self._attributes = {"items": expiring}


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
            total = 0
            for item in items:
                for attr in item.get("attributes", []):
                    total += attr.get("count", 0)
            self._state = total
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
            count = sum(attr.get("count", 0) for attr in item.get("attributes", []))
            locations[loc] = locations.get(loc, 0) + count

        self._attributes = locations
        self._state = sum(locations.values())


class ItemsPerLocationDetailsSensor(Entity):
    """Sensor: Detailliste aller Artikel pro Lagerort für Markdown."""

    def __init__(self, api: SpeisekammerAPI, community_id: str):
        self._api = api
        self._community_id = community_id
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        return "Speisekammer Artikel Details pro Lagerort"

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

        details = {}
        for item in items:
            loc = item.get("location", "Unbekannt")
            if loc not in details:
                details[loc] = []
            for attr in item.get("attributes", []):
                details[loc].append({
                    "name": item.get("name"),
                    "count": attr.get("count", 0),
                    "expires": attr.get("bestBeforeDate"),
                    "gtin": item.get("gtin")
                })

        self._attributes = details
        self._state = sum(len(v) for v in details.values())
