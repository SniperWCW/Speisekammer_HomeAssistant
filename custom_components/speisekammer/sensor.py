from homeassistant.helpers.entity import Entity
from .api import SpeisekammerAPI
from .const import CONF_COMMUNITY_ID
import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    token = config.get("token")
    community_id = config.get(CONF_COMMUNITY_ID)
    api = SpeisekammerAPI(token)
    async_add_entities([StockSensor(api, community_id)], update_before_add=True)


class StockSensor(Entity):
    """Sensor: Artikel pro Lagerort mit Name, Menge, Ablaufdatum, GTIN."""

    def __init__(self, api: SpeisekammerAPI, community_id: str):
        self._api = api
        self._community_id = community_id
        self._state = None
        self._attributes = {}

    @property
    def name(self):
        return "Speisekammer Stock"

    @property
    def state(self):
        # Gesamtanzahl aller Items
        return sum(len(items) for items in self._attributes.values()) if self._attributes else 0

    @property
    def extra_state_attributes(self):
        return self._attributes

    async def async_update(self):
        """Aktualisiert alle Lagerorte und Items."""
        try:
            # Alle Lagerorte abrufen
            storage_locations = await self._api._get(f"communities/{self._community_id}/storage-locations")
        except Exception as e:
            _LOGGER.error("Fehler beim Abrufen der Storage Locations: %s", e)
            self._state = 0
            self._attributes = {}
            return

        all_items = {}
        for loc in storage_locations:
            loc_id = loc.get("id")
            loc_name = loc.get("name", loc_id)
            if not loc_id:
                continue
            try:
                items = await self._api._get(f"stock/{self._community_id}/{loc_id}")
                # Items umstrukturieren
                formatted_items = []
                for item in items:
                    name = item.get("name")
                    gtin = item.get("gtin")
                    for attr in item.get("attributes", []):
                        count = attr.get("count", 0)
                        best_before = attr.get("bestBeforeDate")
                        if best_before:
                            # ISO -> YYYY-MM-DD
                            best_before = datetime.fromisoformat(best_before.replace("Z", "")).date().isoformat()
                        formatted_items.append({
                            "name": name,
                            "count": count,
                            "bestBeforeDate": best_before,
                            "gtin": gtin
                        })
                all_items[loc_name] = formatted_items
            except Exception as e:
                _LOGGER.error("Fehler beim Abrufen der Items für %s: %s", loc_name, e)
                all_items[loc_name] = []

        self._attributes = all_items
        self._state = sum(len(items) for items in all_items.values())
