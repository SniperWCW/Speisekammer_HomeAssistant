from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
import logging

DOMAIN = "speisekammer"
_LOGGER = logging.getLogger(__name__)

class Inventur:
    """Verwaltet die Inventur eines Lagerorts"""

    def __init__(self, hass: HomeAssistant, api, entry_id: str, community_id: str):
        self.hass = hass
        self.api = api
        self.entry_id = entry_id
        self.community_id = community_id
        self._inventur = {}
        self.running = False
        self.location_map = {}  # name -> id

    async def start(self, location_id: str = None):
        """Inventur starten und Artikel aus Lager laden"""
        if not self.community_id:
            _LOGGER.error("Keine Community-ID vorhanden – Inventur kann nicht starten")
            return

        # Location Map erstellen, falls nicht vorhanden
        if not self.location_map:
            locations = await self.api.get_storage_locations(self.community_id)
            self.location_map = {loc["name"]: loc["id"] for loc in locations}
            self.id_to_name_map = {loc["id"]: loc["name"] for loc in locations}

        if not location_id:
            lagerort_entity = self.hass.states.get("input_select.lagerort_auswahl")
            if lagerort_entity:
                name = lagerort_entity.state
                location_id = self.location_map.get(name)
                if not location_id:
                    _LOGGER.warning("Ungültiger Lagerort ausgewählt: %s", name)
                    return
                _LOGGER.info("Lagerort automatisch gewählt: %s (%s)", name, location_id)
            else:
                _LOGGER.warning("Kein Lagerort ausgewählt – Inventur kann nicht starten")
                return

        items = await self.api.get_items(self.community_id, location_id) or []
        self._inventur = {}
        self.running = True
        for item in items:
            total_count = sum(attr.get("count", 0) for attr in item.get("attributes") or [])
            self._inventur[item["gtin"]] = {
                "name": item.get("name") or "Unbekannt",
                "soll": total_count,
                "ist": 0,
                "mhd": (item.get("attributes")[0].get("bestBeforeDate") 
                        if item.get("attributes") else None),
                "lager": self.id_to_name_map.get(location_id, "Unbekannt")
            }
        _LOGGER.info("Inventur gestartet: %d Artikel geladen", len(self._inventur))
        await self._update_state()

    async def scan_article(self, gtin: str, count: int = 1, mhd: str = None):
        _LOGGER.info("Scan: GTIN='%s', aktuelles _inventur keys=%s", gtin, list(self._inventur.keys()))

        """Artikel scannen / Menge erhöhen"""
        if not self.running:
            _LOGGER.warning("Inventur nicht gestartet")
            return
        
        # GTIN auf String trimmen
        gtin = str(gtin).strip()    

        # Wenn Artikel schon existiert, Menge erhöhen
        if gtin in self._inventur:
            self._inventur[gtin]["ist"] += count
            if mhd:
                self._inventur[gtin]["mhd"] = mhd
            return await self._update_state()

        # GTIN in allen Lagerorten suchen
        found = False
        for loc_name, loc_id in self.location_map.items():
            items = await self.api.get_items(self.community_id, loc_id) or []
            for item in items:
                # --- hier GTIN normalisieren ---
                item_gtin = str(item.get("gtin")).strip()
                if item_gtin == gtin:
                    name = item.get("name") or "Unbekannt"
                    soll = sum(attr.get("count", 0) for attr in item.get("attributes") or [])
                    item_mhd = mhd or (item.get("attributes")[0].get("bestBeforeDate") 
                                       if item.get("attributes") else None)
                    self._inventur[gtin] = {
                        "name": name,
                        "soll": soll,
                        "ist": count,
                        "mhd": item_mhd,
                        "lager": loc_name
                    }
                    found = True
                    break
            if found:
                break

        # Wenn nirgendwo gefunden, trotzdem Eintrag erstellen
        if not found:
            self._inventur[gtin] = {
                "name": "Unbekannt",
                "soll": 0,
                "ist": count,
                "mhd": mhd,
                "lager": "Unbekannt"
            }

        await self._update_state()

    async def stop(self):
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
                await self.api.update_stock(
                    self.community_id,
                    self.location_map.get(self._inventur[item["gtin"]]["lager"], 
                                          self._inventur[item["gtin"]]["lager"]),
                    [item]
                )

        _LOGGER.info("Inventur beendet, %d Artikel aktualisiert", len(updated_items))
        self._inventur.clear()
        self.running = False
        await self._update_state()

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

    async def _update_state(self):
        """Aktualisiert den globalen Zustand für Lovelace"""
        self.hass.data.setdefault("speisekammer_inventur", {})
        self.hass.data["speisekammer_inventur"][self.entry_id] = self.get_table_data()


def register_services(hass: HomeAssistant, inventur: Inventur, sensor: 'InventurSensor'):
    """Registriert Inventur-Services in Home Assistant"""

    async def async_start(call):
        await inventur.start(call.data.get("location_id"))
        await sensor.async_update()
        sensor.async_write_ha_state()

    async def async_scan(call):
        await inventur.scan_article(
            call.data["gtin"],
            call.data.get("count", 1),
            call.data.get("mhd")
        )
        await sensor.async_update()
        sensor.async_write_ha_state()

    async def async_stop(call):
        await inventur.stop()
        await sensor.async_update()
        sensor.async_write_ha_state()

    hass.services.async_register(DOMAIN, "start_inventur", async_start)
    hass.services.async_register(DOMAIN, "scan_article", async_scan)
    hass.services.async_register(DOMAIN, "stop_inventur", async_stop)


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
