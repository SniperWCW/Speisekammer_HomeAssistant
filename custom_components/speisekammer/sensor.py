from datetime import datetime, timedelta
from homeassistant.helpers.entity import Entity
from .api import SpeisekammerAPI
from .const import DOMAIN, CONF_TOKEN, CONF_COMMUNITY_ID

async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    token = config.get(CONF_TOKEN)
    community_id = config.get(CONF_COMMUNITY_ID)
    api = SpeisekammerAPI(token=token)

    add_entities([
        ExpiringItemsSensor(api, community_id, days_threshold=3),
        TotalItemsSensor(api, community_id),
        ItemsPerLocationSensor(api, community_id)
    ], True)


class ExpiringItemsSensor(Entity):
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
        items = await self._api.get_items(self._community_id)
        if not items:
            self._state = None
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
        items = await self._api.get_items(self._community_id)
        self._state = len(items) if items else 0


class ItemsPerLocationSensor(Entity):
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
        items = await self._api.get_items(self._community_id)
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