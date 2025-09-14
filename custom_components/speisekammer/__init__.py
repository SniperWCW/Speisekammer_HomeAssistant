"""Speisekammer Integration"""

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .sensor import async_setup_entry as sensors_async_setup_entry

async def async_setup(hass: HomeAssistant, config: dict):
    """Setup der Integration (ConfigFlow, kein YAML)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setup eines ConfigEntry (wird von Home Assistant aufgerufen)."""
    # Sensoren registrieren
    await sensors_async_setup_entry(hass, entry)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload eines ConfigEntry."""
    # Sensoren werden automatisch über HA entfernt
    return True