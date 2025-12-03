import logging
import aiohttp
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import Platform
from homeassistant.components import webhook
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, CONF_URL, CONF_TOKEN, CONF_DEBUG_LOGGING, WEBHOOK_ID_PREFIX, SIGNAL_BUTTON_PRESSED

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.LIGHT, Platform.CLIMATE, Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH, Platform.COVER, Platform.SELECT, Platform.ALARM_CONTROL_PANEL, Platform.BUTTON]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api_url = entry.options.get(CONF_URL, entry.data.get(CONF_URL))
    token = entry.options.get(CONF_TOKEN, entry.data.get(CONF_TOKEN))

    coordinator = TapHomeCoordinator(hass, api_url, token, entry)
    await coordinator.async_get_discovery()
    await coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    webhook_id = f"{WEBHOOK_ID_PREFIX}{entry.entry_id}"
    webhook.async_register(
        hass,
        DOMAIN,
        "TapHome Push",
        webhook_id,
        coordinator.handle_webhook,
        allowed_methods=["POST", "PUT"],
    )
    
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    webhook_id = f"{WEBHOOK_ID_PREFIX}{entry.entry_id}"
    webhook.async_unregister(hass, webhook_id)
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_reload(entry.entry_id)

class TapHomeCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api_url, token, entry):
        super().__init__(
            hass,
            _LOGGER,
            name="TapHome API",
            update_interval=timedelta(seconds=60), 
        )
        self.api_url = api_url
        self.hass = hass
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"TapHome {token}"
        }
        self.devices_config = []
        self.debug_mode = entry.options.get(CONF_DEBUG_LOGGING, False)

    async def async_get_discovery(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_url}/discovery", headers=self.headers) as response:
                    data = await response.json()
                    if isinstance(data, dict) and "devices" in data:
                        self.devices_config = data["devices"]
                    elif isinstance(data, list):
                        self.devices_config = data
                    else:
                        self.devices_config = []
                    
                    if self.debug_mode:
                        _LOGGER.info(f"TapHome: Found {len(self.devices_config)} devices.")
            except Exception as err:
                _LOGGER.error(f"Error during discovery: {err}")

    async def _async_update_data(self):
        # POLLING (Pravidelná kontrola)
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_url}/getAllDevicesValues", headers=self.headers) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"API Error: {response.status}")
                    
                    # DÔLEŽITÉ: push=False -> Toto je len kontrola, nespúšťaj tlačidlá!
                    return self._parse_to_dict(await response.json(), push=False)
            except Exception as err:
                raise UpdateFailed(f"Communication error: {err}")

    def _parse_to_dict(self, data, push=False):
        """Parser. Parameter 'push' určuje, či máme spustiť eventy tlačidiel."""
        parsed_data = {}
        device_list = []
        
        if isinstance(data, dict):
            if "devices" in data:
                device_list = data["devices"]
            elif "deviceId" in data:
                device_list = [data]
        elif isinstance(data, list):
            device_list = data

        for dev in device_list:
            d_id = dev.get("deviceId")
            if d_id is None: continue
            
            if d_id not in parsed_data:
                parsed_data[d_id] = {}
            
            if "values" in dev:
                for val in dev["values"]:
                    type_id = val["valueTypeId"]
                    value = val["value"]

                    # --- LOGIKA PRE TLAČIDLÁ ---
                    # Ak je to ButtonPressed (52) a hodnota je 1 (True)
                    if type_id == 52 and value:
                        # Signál pošleme LEN VTEDY, ak dáta prišli z Webhooku (push=True)
                        # Ak je to z pollingu (push=False), ignorujeme to, aby sa nespúšťali duchovia.
                        if push:
                            async_dispatcher_send(self.hass, SIGNAL_BUTTON_PRESSED.format(d_id))
                        
                        # Vždy continue, aby sa to neuložilo do stavu
                        continue
                        
                    parsed_data[d_id][type_id] = value
        
        return parsed_data

    async def handle_webhook(self, hass, webhook_id, request):
        try:
            data = await request.json()
            if self.debug_mode:
                _LOGGER.debug(f"WEBHOOK PUSH: {data}")
            
            # WEBHOOK: Tu nastavíme push=True, takže tlačidlá budú fungovať
            new_data_fragment = self._parse_to_dict(data, push=True)
            
            if new_data_fragment:
                current_data = self.data if self.data else {}
                updated_data = current_data.copy()
                for d_id, updates in new_data_fragment.items():
                    if d_id not in updated_data:
                        updated_data[d_id] = {}
                    else:
                        updated_data[d_id] = updated_data[d_id].copy()
                    updated_data[d_id].update(updates)
                
                self.async_set_updated_data(updated_data)
            
        except Exception as err:
            _LOGGER.error(f"Error processing webhook: {err}")

    async def async_set_value(self, device_id, type_id, value):
        async with aiohttp.ClientSession() as session:
            url = f"{self.api_url}/setDeviceValue/{device_id}"
            params = {"valueTypeId": type_id, "value": value}
            if self.debug_mode:
                _LOGGER.info(f"SENDING: {url} {params}")
            async with session.get(url, headers=self.headers, params=params) as resp:
                if resp.status != 200:
                     _LOGGER.error(f"Write error: {await resp.text()}")