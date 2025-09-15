from homeassistant import config_entries
import voluptuous as vol
from .api import SpeisekammerAPI

class SpeisekammerConfigFlow(config_entries.ConfigFlow, domain="speisekammer"):
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input:
            api = SpeisekammerAPI(user_input["token"])
            communities = await api.get_communities()
            if communities:
                self.context["token"] = user_input["token"]
                return await self.async_step_select_community(communities)
            else:
                errors["base"] = "invalid_token"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("token"): str}),
            errors=errors
        )

    async def async_step_select_community(self, communities):
        options = {c["id"]: c["name"] for c in communities}
        return self.async_show_form(
            step_id="select_community",
            data_schema=vol.Schema({vol.Required("community_id"): vol.In(options)}),
        )
