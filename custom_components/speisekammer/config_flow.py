import logging
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_TOKEN, CONF_COMMUNITY_ID
from .api import SpeisekammerAPI

_LOGGER = logging.getLogger(__name__)

class SpeisekammerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """ConfigFlow für Speisekammer."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Initial step for user input."""
        errors = {}

        if user_input is not None:
            token = user_input[CONF_TOKEN]
            community_id = user_input[CONF_COMMUNITY_ID]
            api = SpeisekammerAPI(token)

            # Prüfen, ob die Community gültig ist
            try:
                communities = await api.get_communities()
                if community_id not in [c["id"] for c in communities]:
                    errors["base"] = "invalid_community"
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

        else:
            # Schritt 1: nur Token abfragen
            data_schema = vol.Schema({vol.Required(CONF_TOKEN): str})
            return self.async_show_form(step_id="user", data_schema=data_schema)

        # Schritt 2: Community-Auswahl
        if "user_input" in locals() and CONF_TOKEN in user_input:
            token = user_input[CONF_TOKEN]
            api = SpeisekammerAPI(token)
            try:
                communities = await api.get_communities()
                community_dict = {c["id"]: c["name"] for c in communities}
                data_schema = vol.Schema(
                    {vol.Required(CONF_COMMUNITY_ID): vol.In(community_dict)}
                )
                return self.async_show_form(step_id="select_community", data_schema=data_schema)
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)