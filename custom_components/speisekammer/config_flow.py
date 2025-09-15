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
        """Schritt 1: Token abfragen."""
        errors = {}

        if user_input is not None:
            token = user_input[CONF_TOKEN]
            api = SpeisekammerAPI(token)
            try:
                communities = await api.get_communities()
                if len(communities) == 1:
                    # Nur eine Community vorhanden → direkt speichern
                    return self.async_create_entry(
                        title=communities[0]["name"],
                        data={
                            CONF_TOKEN: token,
                            CONF_COMMUNITY_ID: communities[0]["id"]
                        }
                    )
                else:
                    # Mehrere Communities → nächster Schritt
                    self.context["token"] = token
                    community_dict = {c["id"]: c["name"] for c in communities}
                    return self.async_show_form(
                        step_id="select_community",
                        data_schema=vol.Schema({vol.Required(CONF_COMMUNITY_ID): vol.In(community_dict)})
                    )
            except Exception:
                errors["base"] = "cannot_connect"

        # Zeige Eingabeformular für Token
        data_schema = vol.Schema({vol.Required(CONF_TOKEN): str})
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_select_community(self, user_input=None):
        """Schritt 2: Community auswählen."""
        token = self.context.get("token")
        if not token:
            return self.async_abort(reason="missing_token")

        if user_input is not None:
            return self.async_create_entry(
                title="Speisekammer",
                data={
                    CONF_TOKEN: token,
                    CONF_COMMUNITY_ID: user_input[CONF_COMMUNITY_ID]
                }
            )

        return self.async_abort(reason="unknown_error")
