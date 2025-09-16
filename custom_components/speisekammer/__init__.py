import asyncio
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, DATA_CLIENT
from .websocket_client import CrealityWebSocketClient

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    _LOGGER.debug("Setting up %s integration", DOMAIN)
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Creality Assistant from a config entry."""
    _LOGGER.debug("Setting up entry %s", entry.entry_id)
    hass.data[DOMAIN][entry.entry_id] = {}
    data = hass.data[DOMAIN][entry.entry_id]
    data["config"] = entry.data
    # Initialize sensor data with connection status
    data["sensor_data"] = {"connection_status": "DISCONNECTED"}
    _LOGGER.debug("Initial sensor_data: %s", data["sensor_data"])

    # Start the WebSocket client task
    client = CrealityWebSocketClient(hass, entry.entry_id)
    data[DATA_CLIENT] = client
    hass.async_create_task(client.async_run())
    _LOGGER.debug("Started WebSocket client task for entry %s", entry.entry_id)

    # Use the new API to forward setup for the sensor and camera platforms
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "camera"])
    _LOGGER.debug("Forwarded sensor and camera setup for entry %s", entry.entry_id)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.debug("Unloading entry %s", entry.entry_id)
    # Unload the sensor and camera platforms
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    unload_ok &= await hass.config_entries.async_forward_entry_unload(entry, "camera")
    if unload_ok:
        client = hass.data[DOMAIN][entry.entry_id].get(DATA_CLIENT)
        if client:
            await client.async_stop()
            _LOGGER.debug("Stopped WebSocket client for entry %s", entry.entry_id)
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug("Removed data for entry %s", entry.entry_id)
    return unload_ok
