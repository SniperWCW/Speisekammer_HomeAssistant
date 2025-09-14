from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

async def async_setup(hass: HomeAssistant, config: dict):
    """Setup ohne ConfigEntry (optional, falls yaml genutzt wird)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setup über ConfigEntry."""

    # Sensor-Plattform laden (korrekte neue Methode)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True