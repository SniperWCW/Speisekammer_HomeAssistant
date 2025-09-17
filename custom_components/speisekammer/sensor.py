from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event
from .api import SpeisekammerAPI
from .const import DOMAIN, CONF_TOKEN, CONF_COMMUNITY_ID
from .inventur import Inventur, InventurSensor, register_services
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

    # Mapping Lagerort-Name -> ID speichern
    location_map = {loc["name"]: loc["id"] for loc in locations}
    hass.data["speisekammer_location_map"] = location_map

    # Lagerplatz-Sensoren
    for location in locations:
        location_id = location["id"]
        location_name = location["name"]
        entities.append(StorageLocationSensor(api, community_id, location_id, location_name))

    # Single-Item Sensor (GTIN Lookup)
    if locations:
        gtin_sensor = SingleItemSensor(api, community_id)
        gtin_sensor.set_hass(hass)
        entities.append(gtin_sensor)

    # Inventur Sensor
    inventur = Inventur(hass, api)
    register_services(hass, inventur)
    inventur_sensor = InventurSensor(inventur)
    entities.append(inventur_sensor)
    _LOGGER.info("Inventur-Sensor registriert und Services hinzugefügt")

    async_add_entities(entities, update_before_add=True)

    # Service: Artikel hinzufügen
    async def handle_add_item(call):
        gtin = call.data.get("gtin")
        count = call.data.get("count")
        best_before = call.data.get("best_before")
        location_name = call.data.get("location_name")

        # Mapping prüfen, ggf. nachladen
        location_map = hass.data.get("speisekammer_location_map")
        if not location_map:
            locations = await api.get_storage_locations(community_id)
            location_map = {loc["name"]: loc["id"] for loc in locations}
            hass.data["speisekammer_location_map"] = location_map

        location_id = location_map.get(location_name)

        if not location_id:
            _LOGGER.error("Unbekannter Lagerort: %s", location_name)
            return

        try:
            await api.add_item(community_id, location_id, gtin, count, best_before)
            _LOGGER.warning("Artikel hinzugefügt: %s (%s Stück) in %s", gtin, count, location_name)
        except Exception as e:
            _LOGGER.error("Fehler beim Hinzufügen von Artikel %s: %s", gtin, e)

    # Service: Lagerorte für GTIN prüfen
    async def handle_get_locations_for_gtin(call):
        gtin = call.data.get("gtin")
        if not gtin:
            _LOGGER.warning("GTIN fehlt für Lagerortprüfung")
            return

        try:
            locations = await api.get_storage_locations(community_id)
            location_map = {loc["name"]: loc["id"] for loc in locations}
            hass.data["speisekammer_location_map"] = location_map

            matching_locations = []
            for loc in locations:
                item = await api.get_item_by_gtin(community_id, loc["id"], gtin)
                if item:
                    matching_locations.append(loc["name"])

            if not matching_locations:
                matching_locations = [loc["name"] for loc in locations]

            # Input-Select setzen
            import asyncio
            await hass.services.async_call("input_select", "set_options", {
                "entity_id": "input_select.lagerort_auswahl",
                "options": matching_locations
            })
            await asyncio.sleep(0.1)
            await hass.services.async_call("input_select", "select_option", {
                "entity_id": "input_select.lagerort_auswahl",
                "option": matching_locations[0]
            })
            _LOGGER.warning("Lagerorte für GTIN %s gesetzt: %s", gtin, matching_locations)

        except Exception as e:
            _LOGGER.error("Fehler beim Abrufen der Lagerorte für GTIN %s: %s", gtin, e)

    hass.services.async_register(DOMAIN, "add_item", handle_add_item)
    hass.services.async_register(DOMAIN, "get_locations_for_gtin", handle_get_locations_for_gtin)


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
        self._attr_unique_id = f"speisekammer_lagerplatz_{self._location_id}"
        self._attr_icon = "mdi:package-variant"
        self._attr_native_unit_of_measurement = "Artikel"
        self._attr_should_poll = True
        self._state = 0
        self._attr_extra_state_attributes = {
            "table": [],
            "Lagerplatz": location_name,
            "Artikelanzahl": 0
        }

    @property
    def native_value(self):
        return self._state

    async def async_update(self):
        try:
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
                            "Bild": image_url
                        })

            table.sort(key=lambda x: x.get("Ablaufdatum") or "9999-12-31")
            self._state = len(table)
            self._attr_extra_state_attributes = {
                "table": table,
                "Lagerplatz": self._location_name,
                "Artikelanzahl": len(table)
            }

        except Exception as e:
            _LOGGER.error("Fehler beim Update von %s: %s", self._location_name, e)
            self._state = None
            self._attr_extra_state_attributes = {
                "table": [],
                "Lagerplatz": self._location_name,
                "Artikelanzahl": 0
            }


class SingleItemSensor(SensorEntity):
    def __init__(self, api: SpeisekammerAPI, community_id: str):
        self._api = api
        self._community_id = community_id
        self._attr_name = "Speisekammer Artikelabfrage"
        self._attr_unique_id = "speisekammer_gtin_lookup"
        self._attr_icon = "mdi:magnify"
        self._state = "–"
        self._attr_extra_state_attributes = {}

    @property
    def native_value(self):
        return self._state

    def set_hass(self, hass: HomeAssistant):
        self.hass = hass

        # Listener für Änderungen am input_text.gtin_eingabe
        async def state_listener(entity, old_state, new_state):
            await self.async_update()
            self.async_write_ha_state()

        async_track_state_change_event(
            hass,
            "input_text.gtin_eingabe",
            state_listener
        )

    async def async_update(self):
        gtin_state = self.hass.states.get("input_text.gtin_eingabe")
        gtin = gtin_state.state.strip() if gtin_state and gtin_state.state else None

        if not gtin:
            self._state = "Keine GTIN"
            self._attr_extra_state_attributes = {}
            await self.hass.services.async_call("input_number", "set_value", {
                "entity_id": "input_number.menge_eingabe",
                "value": 1
            })
            _LOGGER.warning("Keine GTIN im input_text gefunden")
            return

        found_item = None
        found_location = None
        count_value = 1  # default fallback

        try:
            locations = await self._api.get_storage_locations(self._community_id)
            for loc in locations:
                item = await self._api.get_item_by_gtin(self._community_id, loc["id"], gtin)
                if item:
                    found_item = item
                    found_location = loc["name"]
                    break

            off_data = await fetch_openfoodfacts(gtin)
            image_url = off_data.get("product", {}).get("image_front_small_url") or ""

            if not found_item:
                self._state = "Nicht gefunden"
                self._attr_extra_state_attributes = {
                    "GTIN": gtin,
                    "Bild": image_url,
                    "Lagerplatz": "-",
                    "Menge": 0
                }
                await self.hass.services.async_call("input_number", "set_value", {
                    "entity_id": "input_number.menge_eingabe",
                    "value": 1
                })
                _LOGGER.warning("Kein Item mit GTIN %s gefunden", gtin)
                return

            attr = found_item.get("attributes", [{}])[0]
            count_value = attr.get("count", 1)

            self._state = found_item.get("name", "Unbekannt")
            self._attr_extra_state_attributes = {
                "GTIN": found_item.get("gtin", gtin),
                "Menge": count_value,
                "MHD": attr.get("bestBeforeDate", "–"),
                "Beschreibung": found_item.get("description", ""),
                "Bild": image_url,
                "Lagerplatz": found_location or "-"
            }

            # Menge im input_number setzen
            await self.hass.services.async_call("input_number", "set_value", {
                "entity_id": "input_number.menge_eingabe",
                "value": count_value
            })

            _LOGGER.info("Sensor-State gesetzt auf %s mit Attributen: %s", self._state, self._attr_extra_state_attributes)

        except Exception as e:
            _LOGGER.error("Fehler beim GTIN-Lookup: %s", e)
            self._state = "Fehler"
            self._attr_extra_state_attributes = {
                "GTIN": gtin or "-",
                "Lagerplatz": "-",
                "Menge": 0
            }
            await self.hass.services.async_call("input_number", "set_value", {
                "entity_id": "input_number.menge_eingabe",
                "value": 1
            })

    @property
    def extra_state_attributes(self):
        return self._attr_extra_state_attributes or {}
