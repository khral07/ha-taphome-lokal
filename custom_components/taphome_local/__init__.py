import asyncio
import logging
from datetime import timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import Platform
from homeassistant.components import webhook
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_URL, CONF_TOKEN, CONF_DEBUG_LOGGING, WEBHOOK_ID_PREFIX, SIGNAL_BUTTON_PRESSED

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.LIGHT,
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.COVER,
    Platform.SELECT,
    Platform.ALARM_CONTROL_PANEL,
    Platform.BUTTON,
    Platform.VALVE,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api_url = entry.options.get(CONF_URL, entry.data.get(CONF_URL))
    token = entry.options.get(CONF_TOKEN, entry.data.get(CONF_TOKEN))

    coordinator = TapHomeCoordinator(hass, api_url, token, entry)
    await coordinator.async_get_discovery()
    if not coordinator.devices_config:
        raise ConfigEntryNotReady("TapHome Core unreachable or returned no devices")

    await coordinator.async_config_entry_first_refresh()

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


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    # Allow removal only if the device is no longer reported by the Core.
    # Povoliť odstránenie iba ak zariadenie už nie je hlásené z Core.
    coordinator = hass.data.get(DOMAIN, {}).get(config_entry.entry_id)
    if coordinator is None:
        return True
    active_ids = {str(d.get("deviceId")) for d in coordinator.devices_config}
    for domain, ident in device_entry.identifiers:
        if domain == DOMAIN and ident in active_ids:
            return False
    return True


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
            "Authorization": f"TapHome {token}",
        }
        self.devices_config = []
        self.debug_mode = entry.options.get(CONF_DEBUG_LOGGING, False)
        self._session = async_get_clientsession(hass)

    async def async_get_discovery(self):
        try:
            async with self._session.get(
                f"{self.api_url}/discovery",
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                data = await response.json()
                if isinstance(data, dict) and "devices" in data:
                    self.devices_config = data["devices"]
                elif isinstance(data, list):
                    self.devices_config = data
                else:
                    self.devices_config = []

                if self.debug_mode:
                    _LOGGER.info("TapHome: Found %d devices.", len(self.devices_config))
        except Exception as err:
            _LOGGER.error("Error during discovery: %s", err)
            self.devices_config = []

    async def _async_update_data(self):
        try:
            async with self._session.get(
                f"{self.api_url}/getAllDevicesValues",
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"API Error: {response.status}")
                return self._parse_to_dict(await response.json(), push=False)
        except Exception as err:
            raise UpdateFailed(f"Communication error: {err}")

    def _parse_to_dict(self, data, push=False):
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
            if d_id is None:
                continue

            if d_id not in parsed_data:
                parsed_data[d_id] = {}

            values = dev.get("values")
            # Fallback if event arrives without "values" wrapper.
            # Fallback, ak event príde bez wrappera "values".
            if not values and "valueTypeId" in dev:
                values = [dev]

            for val in values or []:
                type_id = val.get("valueTypeId")
                value = val.get("value")

                # Button events (press 52, hold 38): dispatch signal, don't store.
                # Eventy tlačidiel: poslať signál, neukladať hodnotu.
                if type_id in (52, 38):
                    if push:
                        async_dispatcher_send(
                            self.hass, SIGNAL_BUTTON_PRESSED.format(d_id), type_id
                        )
                    continue

                parsed_data[d_id][type_id] = value

        return parsed_data

    async def handle_webhook(self, hass, webhook_id, request):
        try:
            data = await request.json()
            if self.debug_mode:
                _LOGGER.debug("WEBHOOK PUSH: %s", data)

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
            _LOGGER.error("Error processing webhook: %s", err)

    async def async_set_value(self, device_id, type_id, value):
        url = f"{self.api_url}/setDeviceValue/{device_id}"
        params = {"valueTypeId": type_id, "value": value}
        if self.debug_mode:
            _LOGGER.info("SENDING: %s %s", url, params)

        # Retry once on 503 (TapHome throttles writes under ~500 ms).
        # Jeden pokus znova pri 503 (TapHome obmedzuje zápisy pod ~500 ms).
        for attempt in (0, 1):
            try:
                async with self._session.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 503 and attempt == 0:
                        await asyncio.sleep(0.6)
                        continue
                    if resp.status != 200:
                        _LOGGER.error("Write error %s: %s", resp.status, await resp.text())
                    return
            except Exception as err:
                if attempt == 0:
                    await asyncio.sleep(0.6)
                    continue
                _LOGGER.error("Write exception: %s", err)
                return
