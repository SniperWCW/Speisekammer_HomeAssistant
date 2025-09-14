"""Speisekammer Integration für Home Assistant."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Setup der Integration via configuration.yaml."""
    _LOGGER.debug("Setting up %s integration via YAML", DOMAIN)

    # Lade die Sensorplattform
    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)
    return True


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Setup der Integration via UI (ConfigFlow)."""
    _LOGGER.debug("Setting up %s integration via UI ConfigFlow", DOMAIN)

    # Sensoren anlegen
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Integration beim Entfernen aufräumen."""
    _LOGGER.debug("Unloading %s integration", DOMAIN)
    return await hass.config_entries.async_forward_entry_unload(entry, "sensor")
