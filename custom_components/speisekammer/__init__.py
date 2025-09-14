"""Speisekammer Integration für Home Assistant."""
import logging
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Setup via YAML (Platzhalter)."""
    _LOGGER.debug("Speisekammer Integration: async_setup über YAML")
    return True

async def async_setup_entry(hass, entry):
    """Setup über ConfigFlow / UI."""
    _LOGGER.debug("Speisekammer Integration: async_setup_entry")
    return await hass.config_entries.async_forward_entry_setup(entry, "sensor")

async def async_unload_entry(hass, entry):
    """Integration beim Entfernen aufräumen."""
    _LOGGER.debug("Speisekammer Integration: async_unload_entry")
    return await hass.config_entries.async_forward_entry_unload(entry, "sensor")