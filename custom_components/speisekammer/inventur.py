from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
import logging

_LOGGER = logging.getLogger(__name__)


class Inventur:
    """Verwaltet die Inventur eines Lagerorts"""

    def __init__(self, hass: HomeAssistant, api):
        self.hass = hass
        self.api = api
        self._inventur = {}
        self.running = False

    async def start(self, community_id: str, location_id: str):
        """Inventur starten und Artikel aus Lager laden"""
        items = await self.api.get_items(community_id, location_id)
        self._inventur = {}
        self.running = True
        for item in items:
            total_count = sum(attr.get("count", 0) for attr in item.get("attributes", []))
            self._inventur[item["gtin"]] = {
                "name": item.get("name"),
                "soll": total_count,
                "ist": 0,
                "mhd": item["attributes"][0].get("bestBeforeDate") if item["attributes"] else None,
                "lager": location_id
            }
        _LOGGER.info("Inventur gestartet: %d Artikel geladen", len(self._inventur))

    async def scan_article(self, gtin: str, count: int = 1, mhd: str = None):
        """Artikel scannen / Menge erhöhen"""
        if not self.running:
            _LOGGER.warning("Inventur nicht gestartet")
            return
        if gtin in self._inventur:
            self._inventur[gtin]["ist"] += count
            if mhd:
                self._inventur[gtin]["mhd"] = mhd
        else:
            self._inventur[gtin] = {"name": "Unbekannt", "soll": 0, "ist": count, "mhd": mhd, "lager": "Unbekannt"}

    async def stop(self, community_id: str):
        """Inventur stoppen und Änderungen ins Lager übertragen"""
        if not self.running:
            _LOGGER.warning("Inventur nicht gestartet")
            return

        updated_items = []
        for gtin, data in self._inventur.items():
            if data["ist"] != data["soll"]:
                updated_items.append({
                    "gtin": gtin,
                    "count": data["ist"],
                    "bestBeforeDate": data["mhd"]
                })

        if updated_items:
            for item in updated_items:
                await self.api.update_stock(community_id, self._inventur[item["gtin"]]["lager"], [item])

        _LOGGER.info("Inventur beendet, %d Artikel aktualisiert", len(updated_items))
        self._inventur.clear()
        self.running = False

    def get_table_data(self):
        """Daten für Flex-Table Sensor"""
        return [
            {
                "Name": data["name"],
                "Barcode": gtin,
                "Menge_SOLL": data["soll"],
                "Menge_IST": data["ist"],
                "Lager": data["lager"],
                "MHD": data["mhd"]
            }
            for gtin, data in self._inventur.items()
        ]


def register_services(hass: HomeAssistant, inventur: Inventur):
    """Registriert Inventur-Services in Home Assistant"""

    async def async_start(call):
        await inventur.start(call.data["community_id"], call.data["location_id"])
        entry_id = call.data.get("entry_id", "default")
        hass.data.setdefault("speisekammer_inventur", {})
        hass.data["speisekammer_inventur"][entry_id] = inventur.get_table_data()

    async def async_scan(call):
        await inventur.scan_article(
            call.data["gtin"],
            call.data.get("count", 1),
            call.data.get("mhd")
        )
        entry_id = call.data.get("entry_id", "default")
        hass.data["speisekammer_inventur"][entry_id] = inventur.get_table_data()

    async def async_stop(call):
        await inventur.stop(call.data["community_id"])
        entry_id = call.data.get("entry_id", "default")
        hass.data["speisekammer_inventur"][entry_id] = inventur.get_table_data()

    hass.services.async_register("speisekammer", "start_inventur", async_start)
    hass.services.async_register("speisekammer", "scan_article", async_scan)
    hass.services.async_register("speisekammer", "stop_inventur", async_stop)


class InventurSensor(Entity):
    """Sensor für die Flex-Table-Anzeige der Inventur"""

    def __init__(self, inventur: Inventur):
        self._inventur = inventur
        self._state = "Idle"

    @property
    def name(self):
        return "Speisekammer Inventur"

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return {"table_data": self._inventur.get_table_data()}

    async def async_update(self):
        self._state = "Running" if self._inventur._inventur else "Idle"
