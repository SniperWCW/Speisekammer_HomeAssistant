from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

async def async_setup(hass: HomeAssistant, config: dict):
    """Setup ohne ConfigEntry (nur falls YAML genutzt wird)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setup über ConfigEntry."""
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Entfernen einer ConfigEntry."""
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])