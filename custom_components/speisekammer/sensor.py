from datetime import datetime, timedelta
from homeassistant.helpers.entity import Entity
from .api import SpeisekammerAPI
from .const import DOMAIN, CONF_TOKEN, CONF_COMMUNITY_ID

async def async_setup_platform(hass, config, add_entities, discovery_info=None):
    token = config.get(CONF_TOKEN)
    community_id = config.get(CONF_COMMUNITY_ID)
    api = SpeisekammerAPI(token=token)
    add_entities([ExpiringItemsSensor(api, community_id, days_threshold=3)], True)

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

    def update(self):
        items = self._api.get_items(self._community_id)
        if items is None:
            self._state = None
            return
        now = datetime.utcnow()
        cutoff = now + timedelta(days=self._days)
        expiring = []
        for item in items:
            exp_date_str = item.get("expirationDate") or item.get("expiryDate")  # je nach Feldname
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
            "items": [
                {
                    "name": i.get("name"),
                    "expires": i.get("expirationDate")
                }
                for i in expiring
            ]
        }
