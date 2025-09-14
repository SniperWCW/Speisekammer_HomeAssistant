"""ConfigFlow für Speisekammer Integration."""

import logging
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_TOKEN, CONF_COMMUNITY_ID
from .api import SpeisekammerAPI

_LOGGER = logging.getLogger(__name__)

class SpeisekammerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Speisekammer."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Initial step for user input."""
        errors = {}

        if user_input is not None:
            token = user_input[CONF_TOKEN]
            community_id = user_input[CONF_COMMUNITY_ID]

            api = SpeisekammerAPI(token)
            try:
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
            except Exception:
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_TOKEN): str,
                vol.Required(CONF_COMMUNITY_ID): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )