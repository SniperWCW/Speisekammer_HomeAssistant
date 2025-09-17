from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, CONF_TOKEN, CONF_COMMUNITY_ID
from .api import SpeisekammerAPI
from .inventur import Inventur, InventurSensor, register_services
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setup der Integration über ConfigEntry"""
    hass.data.setdefault(DOMAIN, {})

    token = entry.data[CONF_TOKEN]
    community_id = entry.data[CONF_COMMUNITY_ID]
    api = SpeisekammerAPI(token)

    # Speichere API und Config
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "community_id": community_id,
        "config": entry.data,
    }

    # --- Update Stock Service ---
    async def handle_update_stock(call):
        location_id = call.data.get("location_id")
        items = call.data.get("items")
        _LOGGER.debug("Update stock: location=%s, items=%s", location_id, items)
        await api.update_stock(community_id, location_id, items)
    
    hass.services.async_register(DOMAIN, "update_stock", handle_update_stock)
    _LOGGER.info("Service speisekammer.update_stock registriert")
    
    # --- Inventur Services ---
    # Wir erstellen die Inventur hier, Sensor wird in sensor.py registriert
    inventur = Inventur(hass, api, entry_id=entry.entry_id, community_id=community_id)
    # Sensor wird erst in sensor.py erzeugt, wir übergeben inventur nur an register_services
    # register_services wird von sensor.py aufgerufen, daher hier nicht nötig

    # Sensor Plattform forwarden
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Integration entladen"""
    await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
