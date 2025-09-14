async def async_step_user(self, user_input=None):
    """Initial setup via UI."""
    errors = {}

    if user_input is not None:
        token = user_input[CONF_TOKEN]

        api = SpeisekammerAPI(token)
        try:
            communities = await api.get_communities()
            if not communities:
                errors["base"] = "cannot_connect"
            else:
                # Automatisch erste Community auswählen
                community_id = communities[0]["id"]

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

    # Formular: nur Token eingeben
    data_schema = vol.Schema(
        {vol.Required(CONF_TOKEN): str}
    )

    return self.async_show_form(
        step_id="user",
        data_schema=data_schema,
        errors=errors
    )