import logging
from homeassistant import config_entries
from .const import DOMAIN, CONF_TOKEN, CONF_COMMUNITY_ID
from .api import SpeisekammerAPI
from aiohttp import ClientError
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

class SpeisekammerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """ConfigFlow für Speisekammer."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None and CONF_COMMUNITY_ID in user_input:
            # Benutzer hat Community ausgewählt
            token = user_input[CONF_TOKEN]
            community_id = user_input[CONF_COMMUNITY_ID]
            return self.async_create_entry(
                title="Speisekammer",
                data={
                    CONF_TOKEN: token,
                    CONF_COMMUNITY_ID: community_id
                }
            )

        elif user_input is not None:
            # Token wurde eingegeben, Communities abrufen
            token = user_input[CONF_TOKEN]
            api = SpeisekammerAPI(token)
            try:
                communities = await api.get_communities()
                if not communities:
                    errors["base"] = "cannot_connect"
                elif len(communities) == 1:
                    # Nur eine Community → direkt anlegen
                    return self.async_create_entry(
                        title="Speisekammer",
                        data={
                            CONF_TOKEN: token,
                            CONF_COMMUNITY_ID: communities[0]["id"]
                        }
                    )
                else:
                    # Mehrere Communities → Auswahl anzeigen
                    options = {c["id"]: c["name"] for c in communities}
                    data_schema = vol.Schema({
                        vol.Required(CONF_COMMUNITY_ID): vol.In(options),
                        vol.Required(CONF_TOKEN, default=token): str
                    })
                    return self.async_show_form(
                        step_id="user",
                        data_schema=data_schema
                    )

            except ClientError:
                errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.exception("Fehler beim Abrufen der Communities: %s", e)
                errors["base"] = "unknown"

        # Initialformular nur für Token
        data_schema = vol.Schema({vol.Required(CONF_TOKEN): str})
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)