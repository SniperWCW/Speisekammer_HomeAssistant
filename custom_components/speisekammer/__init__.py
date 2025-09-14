import logging
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_TOKEN, CONF_COMMUNITY_ID
from .api import SpeisekammerAPI

_LOGGER = logging.getLogger(__name__)

class SpeisekammerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """ConfigFlow für Speisekammer."""

    VERSION = 1

    def __init__(self):
        self._token = None
        self._communities = None

    async def async_step_user(self, user_input=None):
        """Schritt 1: Token abfragen."""
        errors = {}

        if user_input is not None:
            self._token = user_input[CONF_TOKEN]
            api = SpeisekammerAPI(self._token)

            try:
                self._communities = await api.get_communities()

                if not self._communities:
                    errors["base"] = "no_communities"
                elif len(self._communities) == 1:
                    # Direkt Community setzen
                    return self.async_create_entry(
                        title="Speisekammer",
                        data={
                            CONF_TOKEN: self._token,
                            CONF_COMMUNITY_ID: self._communities[0]["id"]
                        }
                    )
                else:
                    # Mehrere Communities → Auswahl anbieten
                    return await self.async_step_select_community()
            except Exception:
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema({vol.Required(CONF_TOKEN): str})
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_select_community(self, user_input=None):
        """Schritt 2: Auswahl der Community."""
        errors = {}

        if user_input is not None:
            community_id = user_input[CONF_COMMUNITY_ID]
            return self.async_create_entry(
                title="Speisekammer",
                data={
                    CONF_TOKEN: self._token,
                    CONF_COMMUNITY_ID: community_id
                }
            )

        community_dict = {c["id"]: c["name"] for c in self._communities}
        data_schema = vol.Schema(
            {vol.Required(CONF_COMMUNITY_ID): vol.In(community_dict)}
        )

        return self.async_show_form(step_id="select_community", data_schema=data_schema, errors=errors)
