import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.network import get_url
import aiohttp

from .const import DOMAIN, CONF_URL, CONF_TOKEN, CONF_DEBUG_LOGGING, WEBHOOK_ID_PREFIX

class TapHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            valid = await self._test_connection(user_input[CONF_URL], user_input[CONF_TOKEN])
            if valid:
                return self.async_create_entry(title="TapHome", data=user_input)
            else:
                errors["base"] = "cannot_connect"

        schema = vol.Schema({
            vol.Required(CONF_URL, default="http://192.168.1.x/api/TapHomeApi/v1"): str,
            vol.Required(CONF_TOKEN): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def _test_connection(self, url, token):
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
    def __init__(self, config_entry):
        """Initialize options flow."""
        # Uložíme config_entry bezpečne
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            user_input.pop("webhook_url_display", None)
            return self.async_create_entry(title="", data=user_input)

        # BEZPEČNÉ NAČÍTANIE: Ak kľúč neexistuje, použijeme prázdny string alebo False
        # Toto zabráni chybe 500
        current_url = self._config_entry.options.get(CONF_URL, self._config_entry.data.get(CONF_URL, ""))
        current_token = self._config_entry.options.get(CONF_TOKEN, self._config_entry.data.get(CONF_TOKEN, ""))
        current_debug = self._config_entry.options.get(CONF_DEBUG_LOGGING, False)

        # Generovanie URL
        webhook_id = f"{WEBHOOK_ID_PREFIX}{self._config_entry.entry_id}"
        try:
            base_url = get_url(self.hass, allow_internal=True, allow_external=True)
        except Exception:
            base_url = "http://<YOUR_HA_IP>:8123"
        
        full_webhook_url = f"{base_url}/api/webhook/{webhook_id}"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_URL, default=current_url): str,
                vol.Required(CONF_TOKEN, default=current_token): str,
                vol.Required(CONF_DEBUG_LOGGING, default=current_debug): bool,
                vol.Optional("webhook_url_display", description={"suggested_value": full_webhook_url}): str,
            })
        )