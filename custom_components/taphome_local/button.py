import time

import homeassistant.util.dt as dt_util
from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import DOMAIN
from .entity import TapHomeEntity
from .const import SIGNAL_BUTTON_PRESSED


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices_config:
        supported_values = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        device_type = device.get("type", "")

        if 52 in supported_values or "PushButton" in device_type:
            entities.append(TapHomeButton(coordinator, device))

    async_add_entities(entities)


class TapHomeButton(TapHomeEntity, ButtonEntity):
    _attr_device_class = ButtonDeviceClass.IDENTIFY

    def __init__(self, coordinator, device_config):
        super().__init__(coordinator, device_config)
        self._attr_unique_id = f"taphome_button_{self.device_id}"
        # Debounce window for UI echo from webhook. / Debounce okno pre echo z webhooku.
        self._last_ui_press = 0.0

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_BUTTON_PRESSED.format(self.device_id),
                self._handle_physical_press,
            )
        )

    @callback
    def _handle_physical_press(self, type_id=None):
        # Ignore webhook echo within 2s of our own UI press. / Ignoruj echo do 2 s od UI stlačenia.
        if time.time() - self._last_ui_press < 2.0:
            return
        self._attr_last_pressed = dt_util.utcnow()
        self.async_write_ha_state()

    async def async_press(self) -> None:
        self._last_ui_press = time.time()

        supported_values = [v['valueTypeId'] for v in self.device_config.get('supportedValues', [])]
        target_id = 52
        if 52 not in supported_values and 48 in supported_values:
            target_id = 48

        await self.coordinator.async_set_value(self.device_id, target_id, 1)

        self._attr_last_pressed = dt_util.utcnow()
        self.async_write_ha_state()

        await self.coordinator.async_request_refresh()
