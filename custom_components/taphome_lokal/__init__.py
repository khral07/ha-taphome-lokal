import logging
import aiohttp
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import Platform

from .const import DOMAIN, CONF_URL, CONF_TOKEN, CONF_DEBUG_LOGGING

_LOGGER = logging.getLogger(__name__)

# List of supported platforms / Zoznam podporovaných platforiem
PLATFORMS = [Platform.LIGHT, Platform.CLIMATE, Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH, Platform.COVER, Platform.SELECT, Platform.ALARM_CONTROL_PANEL]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Start the integration via GUI. / Spustenie integrácie cez GUI.
    api_url = entry.data[CONF_URL]
    token = entry.data[CONF_TOKEN]

    # Create and store the coordinator / Vytvoríme koordinátora a uložíme ho
    coordinator = TapHomeCoordinator(hass, api_url, token, entry)
    
    # Initial load / Prvotné načítanie
    await coordinator.async_get_discovery()
    await coordinator.async_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Load platforms (light, climate...) / Načítame platformy (svetlá, klíma...)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Add listener for settings changes / Pridáme poslucháča na zmeny nastavení
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Cleanup when removing the integration. / Vyčistenie pri odstránení integrácie.
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    # Restart on settings change (e.g. enable debug log). / Reštart pri zmene nastavení (napr. zapnutie debug logu).
    await hass.config_entries.async_reload(entry.entry_id)

class TapHomeCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api_url, token, entry):
        super().__init__(
            hass,
            _LOGGER,
            name="TapHome API",
            update_interval=timedelta(seconds=2), 
        )
        self.api_url = api_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"TapHome {token}"
        }
        self.devices_config = []
        # Check if debug log is enabled in integration settings / Zistíme, či je zapnutý debug log v nastaveniach integrácie
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
                        _LOGGER.info(f"TapHome: Found {len(self.devices_config)} devices. / Našiel som {len(self.devices_config)} zariadení.")
            except Exception as err:
                _LOGGER.error(f"Error during discovery / Chyba pri discovery: {err}")

    async def _async_update_data(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_url}/getAllDevicesValues", headers=self.headers) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"API Error: {response.status}")
                        
                    data = await response.json()
                    parsed_data = {}
                    
                    device_list = []
                    if isinstance(data, dict) and "devices" in data:
                        device_list = data["devices"]
                    elif isinstance(data, list):
                        device_list = data

                    for dev in device_list:
                        d_id = dev.get("deviceId")
                        if d_id is None: continue
                        if d_id not in parsed_data:
                            parsed_data[d_id] = {}
                        if "values" in dev:
                            for val in dev["values"]:
                                parsed_data[d_id][val["valueTypeId"]] = val["value"]
                    
                    # Log only if enabled in GUI / Logovanie iba ak je zapnuté v GUI
                    if self.debug_mode:
                        _LOGGER.debug(f"Received data sample / Prijaté dáta (vzorka): {str(parsed_data)[:100]}...")
                        
                    return parsed_data
            except Exception as err:
                raise UpdateFailed(f"Communication error / Chyba komunikácie: {err}")

    async def async_set_value(self, device_id, type_id, value):
        async with aiohttp.ClientSession() as session:
            # Use GET method with params in URL according to documentation / Používame GET metódu s parametrami v URL podľa dokumentácie
            url = f"{self.api_url}/setDeviceValue/{device_id}"
            params = {"valueTypeId": type_id, "value": value}
            
            if self.debug_mode:
                _LOGGER.info(f"SENDING / ODOSIELAM: {url} {params}")
            
            async with session.get(url, headers=self.headers, params=params) as resp:
                if resp.status != 200:
                     _LOGGER.error(f"Write error / Chyba zápisu: {await resp.text()}")