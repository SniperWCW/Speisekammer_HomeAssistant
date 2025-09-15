from homeassistant.helpers.entity import SensorEntity
from .const import DOMAIN
from .api import SpeisekammerAPI

async def async_setup_entry(hass, entry, async_add_entities):
    token = entry.data["token"]
    community_id = entry.data["community_id"]
    api = SpeisekammerAPI(token)
    locations = await api.get_storage_locations(community_id)

    sensors = []
    for location in locations:
        sensors.append(StorageLocationSensor(location))
    async_add_entities(sensors)

class StorageLocationSensor(SensorEntity):
    def __init__(self, location):
        self._location = location
        self._name = f"Lagerplatz: {location['name']}"
        self._state = None
        self._attributes = {}

    async def async_update(self):
        items = self._location.get("items", [])
        self._state = sum(item["amount"] for item in items)
        self._attributes = {
            "table": [
                {
                    "Name": item["name"],
                    "Menge": item["amount"],
                    "GTIN": item.get("gtin", ""),
                    "Ablaufdatum": item.get("expirationDate", "")
                }
                for item in items
            ]
        }

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes
