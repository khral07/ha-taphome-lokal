import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import aiohttp

from .const import DOMAIN, CONF_URL, CONF_TOKEN, CONF_DEBUG_LOGGING

class TapHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    # Handles adding the integration via the GUI. / Spracováva pridanie integrácie cez grafické rozhranie (GUI).
    VERSION = 1

    async def async_step_user(self, user_input=None):
        # First step: Form for URL and Token. / Prvý krok: Formulár pre URL a Token.
        errors = {}

        if user_input is not None:
            # Validate connection / Overíme, či údaje fungujú
            valid = await self._test_connection(user_input[CONF_URL], user_input[CONF_TOKEN])
            if valid:
                return self.async_create_entry(title="TapHome", data=user_input)
            else:
                errors["base"] = "cannot_connect"

        # Form schema / Schéma formulára
        schema = vol.Schema({
            vol.Required(CONF_URL, default="http://192.168.1.x/api/TapHomeApi/v1"): str,
            vol.Required(CONF_TOKEN): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def _test_connection(self, url, token):
        # Quick connection test. / Rýchly test pripojenia.
        try:
            headers = {"Authorization": f"TapHome {token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/discovery", headers=headers, timeout=5) as resp:
                    return resp.status == 200
        except Exception:
            return False

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return TapHomeOptionsFlowHandler(config_entry)

class TapHomeOptionsFlowHandler(config_entries.OptionsFlow):
    # Handles the 'Configure' button (Settings). / Spracováva tlačidlo 'Konfigurovať' (Nastavenia).

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Load current value, default is False / Načítame aktuálnu hodnotu, predvolená je False
        current_debug = self.config_entry.options.get(CONF_DEBUG_LOGGING, False)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_DEBUG_LOGGING, default=current_debug): bool
            })
        )