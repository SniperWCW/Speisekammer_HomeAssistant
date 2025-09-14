"""Speisekammer Integration"""
from homeassistant.core import HomeAssistant

DOMAIN = "speisekammer"

async def async_setup(hass: HomeAssistant, config: dict):
    """Setup der Integration über ConfigFlow (kein YAML)."""
    return True
