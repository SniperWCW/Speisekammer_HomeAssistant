"""ConfigFlow für Speisekammer Integration."""
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_TOKEN, CONF_COMMUNITY_ID
from .api import SpeisekammerAPI
from aiohttp import ClientError

_LOGGER = logging.getLogger(__name__)

class SpeisekammerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Speisekammer."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Initial setup via UI."""
        errors = {}

        if user_input is not None:
            token = user_input[CONF_TOKEN]
            community_id = user_input[CONF_COMMUNITY_ID]

            api = SpeisekammerAPI(token)
            try:
                # Testaufruf: Communities abrufen
                communities = await api.get_communities()
                if not communities:
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                        title="Speisekammer",
                        data={
                            CONF_TOKEN: token,
                            CONF_COMMUNITY_ID: community_id
                        }
                    )
            except ClientError:
                errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.exception("Fehler beim Abrufen der Communities: %s", e)
                errors["base"] = "unknown"

        # Formular für UI
        data_schema = vol.Schema(
            {
                vol.Required(CONF_TOKEN): str,
                vol.Required(CONF_COMMUNITY_ID): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )