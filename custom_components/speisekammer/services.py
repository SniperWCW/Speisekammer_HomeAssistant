from homeassistant.helpers import service

async def async_setup_services(hass, api: SpeisekammerAPI):
    async def handle_update_item(call):
        gtin = call.data.get("gtin")
        description = call.data.get("description")
        count = call.data.get("count")
        best_before = call.data.get("best_before")

        community_id = call.data.get("community_id")
        await api.update_item(community_id, gtin, description, count, best_before)

    hass.services.async_register(
        "speisekammer",
        "update_item",
        handle_update_item,
        schema=vol.Schema({
            vol.Required("gtin"): str,
            vol.Required("description"): str,
            vol.Required("count"): int,
            vol.Optional("best_before"): str,
            vol.Required("community_id"): str
        })
    )
