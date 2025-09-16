from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .api import SpeisekammerAPI
from .const import DOMAIN, CONF_TOKEN, CONF_COMMUNITY_ID
import logging
import aiohttp

_LOGGER = logging.getLogger(__name__)
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

    if locations:
        gtin_sensor = SingleItemSensor(api, community_id, locations[0]["id"])
        gtin_sensor.set_hass(hass)
        entities.append(gtin_sensor)

    async_add_entities(entities, update_before_add=True)

async def fetch_openfoodfacts(gtin: str) -> dict:
    url = f"https://world.openfoodfacts.org/api/v2/product/{gtin}.json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
    except Exception as e:
        _LOGGER.warning("OpenFoodFacts Fehler für GTIN %s: %s", gtin, e)
    return {}

class StorageLocationSensor(SensorEntity):
    def __init__(self, api: SpeisekammerAPI, community_id: str, location_id: str, location_name: str):
        self._api = api
        self._community_id = community_id
        self._location_id = location_id
        self._location_name = location_name

        self._attr_name = f"Lagerplatz: {location_name}"
        self._attr_unique_id = f"speisekammer_lagerplatz_{location_id}"
        self._attr_icon = "mdi:package-variant"
        self._attr_unit_of_measurement = "Artikel"
        self._attr_should_poll = True
        self._attr_state = 0
        self._attr_extra_state_attributes = {
            "table": [],
            "Lagerplatz": location_name,
            "Artikelanzahl": 0
        }

    async def async_update(self):
        items = await self._api.get_items(self._community_id, self._location_id)
        table = []

        for item in items or []:
            for attr in item.get("attributes", []):
                count = attr.get("count", 0)
                if count > 0:
                    gtin = item.get("gtin", "")
                    off_data = await fetch_openfoodfacts(gtin) if gtin else {}
                    image_url = off_data.get("product", {}).get("image_front_small_url", "")

                    table.append({
                        "Name": item.get("name", "Unbekannt"),
                        "Menge": count,
                        "GTIN": gtin,
                        "Ablaufdatum": attr.get("bestBeforeDate", ""),
                        "Lagerplatz": self._location_name,
                        "image_front_small_url": image_url
                    })

        table.sort(key=lambda x: x.get("Ablaufdatum") or "")
        self._attr_state = len(table)
        self._attr_extra_state_attributes = {
            "table": table,
            "Lagerplatz": self._location_name,
            "Artikelanzahl": len(table)
        }

class SingleItemSensor(SensorEntity):
    def __init__(self, api: SpeisekammerAPI, community_id: str, location_id: str):
        self._api = api
        self._community_id = community_id
        self._location_id = location_id
        self._attr_name = "Speisekammer Artikelabfrage"
        self._attr_unique_id = "speisekammer_gtin_lookup"
        self._attr_icon = "mdi:magnify"
        self._attr_state = 0
        self._attr_extra_state_attributes = {}

    def set_hass(self, hass: HomeAssistant):
        self.hass = hass

    async def async_update(self):
        gtin_state = self.hass.states.get("input_text.gtin_abfrage")
        gtin = gtin_state.state.strip() if gtin_state and gtin_state.state else None

        if not gtin:
            self._attr_state = "Keine GTIN"
            self._attr_extra_state_attributes = {}
            return

        item = await self._api.get_item_by_gtin(self._community_id, self._location_id, gtin)
        off_data = await fetch_openfoodfacts(gtin)
        image_url = off_data.get("product", {}).get("image_front_small_url", "")

        if not item:
            self._attr_state = "Nicht gefunden"
            self._attr_extra_state_attributes = {
                "GTIN": gtin,
                "Bild": image_url
            }
            return

        attr = item.get("attributes", [{}])[0]
        self._attr_state = item.get("name", "Unbekannt")
        self._attr_extra_state_attributes = {
            "GTIN": item.get("gtin", gtin),
            "Menge": attr.get("count", 0),
            "MHD": attr.get("bestBeforeDate", "–"),
            "Beschreibung": item.get("description", ""),
            "Bild": image_url
        }
