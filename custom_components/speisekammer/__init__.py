from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, CONF_TOKEN, CONF_COMMUNITY_ID
from .api import SpeisekammerAPI
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})

    token = entry.data[CONF_TOKEN]
    community_id = entry.data[CONF_COMMUNITY_ID]
    api = SpeisekammerAPI(token)

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "config": entry.data
    }

    async def handle_update_stock(call):
        location_id = call.data.get("location_id")
        items = call.data.get("items")
        _LOGGER.debug("Update stock: location=%s, items=%s", location_id, items)
        await api.update_stock(community_id, location_id, items)

    hass.services.async_register(DOMAIN, "update_stock", handle_update_stock)
    _LOGGER.info("Service speisekammer.update_stock erfolgreich registriert")

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
