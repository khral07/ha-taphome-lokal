import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.network import get_url
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_URL,
    CONF_TOKEN,
    CONF_DEBUG_LOGGING,
    WEBHOOK_ID_PREFIX,
    CONF_EXPOSE_AS_LIGHT,
    CONF_EXPOSE_AS_VALVE,
    CONF_EXPOSE_AS_SWITCH,
    CONF_EXPOSE_AS_COVER,
)


class TapHomeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            valid = await self._test_connection(user_input[CONF_URL], user_input[CONF_TOKEN])
            if valid:
                # Unikátne ID z Core (locationId) bráni duplicitnému pridaniu rovnakého Core.
                # Unique ID from the Core (locationId) prevents adding the same Core twice.
                loc_id = await self._get_location_id(user_input[CONF_URL], user_input[CONF_TOKEN])
                if loc_id:
                    await self.async_set_unique_id(loc_id)
                    self._abort_if_unique_id_configured()
                return self.async_create_entry(title="TapHome", data=user_input)
            errors["base"] = "cannot_connect"

        schema = vol.Schema({
            vol.Required(CONF_URL, default="http://192.168.1.x/api/TapHomeApi/v1"): str,
            vol.Required(CONF_TOKEN): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data):
        # Spustí sa, keď API vráti 401 (neplatný token). / Triggered when the API returns 401.
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        errors = {}
        entry = self._reauth_entry
        url = entry.options.get(CONF_URL, entry.data.get(CONF_URL))
        if user_input is not None:
            if await self._test_connection(url, user_input[CONF_TOKEN]):
                self.hass.config_entries.async_update_entry(
                    entry, data={**entry.data, CONF_TOKEN: user_input[CONF_TOKEN]}
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")
            errors["base"] = "cannot_connect"
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            errors=errors,
        )

    async def _test_connection(self, url, token):
        try:
            headers = {"Authorization": f"TapHome {token}"}
            session = async_get_clientsession(self.hass)
            async with session.get(
                f"{url}/discovery",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def _get_location_id(self, url, token):
        # Vráti locationId z /location, alebo None. / Returns locationId from /location, or None.
        try:
            headers = {"Authorization": f"TapHome {token}"}
            session = async_get_clientsession(self.hass)
            async with session.get(
                f"{url}/location",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return str(data.get("locationId")) if isinstance(data, dict) else None
        except Exception:
            return None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return TapHomeOptionsFlowHandler(config_entry)


class TapHomeOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            user_input.pop("webhook_url_display", None)
            return self.async_create_entry(title="", data=user_input)

        current_url = self._config_entry.options.get(CONF_URL, self._config_entry.data.get(CONF_URL, ""))
        current_token = self._config_entry.options.get(CONF_TOKEN, self._config_entry.data.get(CONF_TOKEN, ""))
        current_debug = self._config_entry.options.get(CONF_DEBUG_LOGGING, False)

        curr_lights = self._config_entry.options.get(CONF_EXPOSE_AS_LIGHT, [])
        curr_valves = self._config_entry.options.get(CONF_EXPOSE_AS_VALVE, [])
        curr_switches = self._config_entry.options.get(CONF_EXPOSE_AS_SWITCH, [])
        curr_covers = self._config_entry.options.get(CONF_EXPOSE_AS_COVER, [])

        devices_dict = {}
        coordinator = getattr(self._config_entry, "runtime_data", None)

        if coordinator and coordinator.devices_config:
            devices_dict = {
                str(dev["deviceId"]): f"{dev['name']} (ID: {dev['deviceId']})"
                for dev in coordinator.devices_config
            }

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

                vol.Optional(CONF_EXPOSE_AS_LIGHT, default=curr_lights): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": k, "label": v} for k, v in devices_dict.items()],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_EXPOSE_AS_COVER, default=curr_covers): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": k, "label": v} for k, v in devices_dict.items()],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_EXPOSE_AS_VALVE, default=curr_valves): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": k, "label": v} for k, v in devices_dict.items()],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_EXPOSE_AS_SWITCH, default=curr_switches): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": k, "label": v} for k, v in devices_dict.items()],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),

                vol.Optional("webhook_url_display", description={"suggested_value": full_webhook_url}): str,
            })
        )
