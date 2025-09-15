from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .api import SpeisekammerAPI
from .const import DOMAIN, CONF_TOKEN, CONF_COMMUNITY_ID

# ⏱️ Sensor wird alle 10 Minuten aktualisiert
SCAN_INTERVAL = timedelta(minutes=10)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    token = entry.data[CONF_TOKEN]
    community_id = entry.data[CONF_COMMUNITY_ID]
    api = SpeisekammerAPI(token=token)

    locations = await api.get_storage_locations(community_id)
    entities = []

    for location in locations:
        location_id = location["id"]
        location_name = location["name"]
        entities.append(StorageLocationSensor(api, community_id, location_id, location_name))

    async_add_entities(entities, update_before_add=True)

class StorageLocationSensor(SensorEntity):
    """Sensor für einen Lagerort mit flex-table-kompatiblen Attributen."""

    def __init__(self, api: SpeisekammerAPI, community_id: str, location_id: str, location_name: str):
        self._api = api
        self._community_id = community_id
        self._location_id = location_id
        self._location_name = location_name

        self._attr_name = f"Lagerplatz: {location_name}"
        self._attr_unique_id = f"speisekammer_{location_id}"
        self._attr_icon = "mdi:package-variant"
        self._attr_unit_of_measurement = "Artikel"
        self._attr_state = None
        self._attr_extra_state_attributes = {}

    async def async_update(self):
        items = await self._api.get_items(self._community_id, self._location_id)
        if not items:
            self._attr_state = 0
            self._attr_extra_state_attributes = {
                "table": [],
                "Lagerplatz": self._location_name,
                "Artikelanzahl": 0
            }
            return

        table = []
        for item in items:
            for attr in item.get("attributes", []):
                if attr.get("count", 0) > 0:
                    table.append({
                        "Name": item.get("name", "Unbekannt"),
                        "Menge": attr.get("count", 1),
                        "GTIN": item.get("gtin", ""),
                        "Ablaufdatum": attr.get("bestBeforeDate", "")
                    })

        self._attr_state = len(table)
        self._attr_extra_state_attributes = {
            "table": table,
            "Lagerplatz": self._location_name,
            "Artikelanzahl": len(table)
        }
