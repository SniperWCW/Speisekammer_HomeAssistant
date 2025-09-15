from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN, CONF_TOKEN, CONF_COMMUNITY_ID
from .api import SpeisekammerAPI

class SpeisekammerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            token = user_input[CONF_TOKEN]
            api = SpeisekammerAPI(token)
            communities = await api.get_communities()

            if communities:
                self._token = token
                self._communities = communities
                return await self.async_step_select_community()
            else:
                errors["base"] = "invalid_token"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_TOKEN): str
            }),
            errors=errors
        )

    async def async_step_select_community(self, user_input=None):
        errors = {}
        community_options = {
            c["id"]: c["name"] for c in self._communities
        }

        if user_input is not None:
            community_id = user_input[CONF_COMMUNITY_ID]
            return self.async_create_entry(
                title=community_options[community_id],
                data={
                    CONF_TOKEN: self._token,
                    CONF_COMMUNITY_ID: community_id
                }
            )

        return self.async_show_form(
            step_id="select_community",
            data_schema=vol.Schema({
                vol.Required(CONF_COMMUNITY_ID): vol.In(community_options)
            }),
            errors=errors
        )
