from homeassistant.components.light import (
    LightEntity,
    ColorMode,
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR,
)

from . import DOMAIN
from .entity import TapHomeEntity
from .const import CONF_EXPOSE_AS_LIGHT


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data

    forced_lights = entry.options.get(CONF_EXPOSE_AS_LIGHT, [])

    entities = []
    for device in coordinator.devices_config:
        dev_id = str(device["deviceId"])
        supported_ids = [v['valueTypeId'] for v in device.get('supportedValues', [])]

        has_brightness = (65 in supported_ids) or (42 in supported_ids)
        has_cct = (89 in supported_ids)
        has_color = (40 in supported_ids) and (41 in supported_ids)
        is_lighting_category = device.get("category") == "OSVETLENIE"

        if has_brightness or has_cct or has_color or is_lighting_category or (dev_id in forced_lights):
            entities.append(TapHomeLight(coordinator, device))

    async_add_entities(entities)


class TapHomeLight(TapHomeEntity, LightEntity):
    def __init__(self, coordinator, device_config):
        super().__init__(coordinator, device_config)
        self._attr_unique_id = f"taphome_light_{self.device_id}"

        self.supported_val_ids = [v['valueTypeId'] for v in device_config.get('supportedValues', [])]

        if 65 in self.supported_val_ids:
            self._brightness_id = 65
        elif 42 in self.supported_val_ids:
            self._brightness_id = 42
        else:
            self._brightness_id = None

        self._cct_id = 89 if 89 in self.supported_val_ids else None
        self._hue_id = 40 if 40 in self.supported_val_ids else None
        self._sat_id = 41 if 41 in self.supported_val_ids else None

        self._min_kelvin = 2700
        self._max_kelvin = 6500
        if self._cct_id:
            for val in device_config.get("supportedValues", []):
                if val["valueTypeId"] == 89:
                    self._min_kelvin = int(val.get("minValue", 2700))
                    self._max_kelvin = int(val.get("maxValue", 6500))
                    break

    @property
    def is_on(self):
        val = self._get_val(48)
        if val is None and self._brightness_id:
            bright = self._get_val(self._brightness_id)
            return (bright or 0) > 0
        return val == 1 if val is not None else False

    @property
    def brightness(self):
        if self._brightness_id:
            val = self._get_val(self._brightness_id)
            if val is not None:
                return int(val * 255)
        return None

    @property
    def color_temp_kelvin(self):
        if self._cct_id:
            val = self._get_val(self._cct_id)
            if val:
                return int(val)
        return None

    @property
    def hs_color(self):
        if self._hue_id and self._sat_id:
            hue = self._get_val(self._hue_id)
            sat = self._get_val(self._sat_id)
            if hue is not None and sat is not None:
                # TapHome saturation is always 0.0–1.0. / Sýtosť z TapHome je vždy 0.0–1.0.
                return (hue, sat * 100)
        return None

    @property
    def min_color_temp_kelvin(self):
        return self._min_kelvin

    @property
    def max_color_temp_kelvin(self):
        return self._max_kelvin

    @property
    def supported_color_modes(self):
        modes = set()
        if self._hue_id and self._sat_id:
            modes.add(ColorMode.HS)
        if self._cct_id:
            modes.add(ColorMode.COLOR_TEMP)
        if not modes and self._brightness_id:
            modes.add(ColorMode.BRIGHTNESS)
        if not modes:
            modes.add(ColorMode.ONOFF)
        return modes

    @property
    def color_mode(self):
        if self._hue_id and self._sat_id:
            return ColorMode.HS
        if self._cct_id:
            return ColorMode.COLOR_TEMP
        if self._brightness_id:
            return ColorMode.BRIGHTNESS
        return ColorMode.ONOFF

    def _get_val(self, type_id):
        data = self.coordinator.data or {}
        dev_data = data.get(self.device_id, {})
        return dev_data.get(type_id)

    async def async_turn_on(self, **kwargs):
        # Collect all requested changes and send them in ONE batched request, so
        # colour + brightness + ON happen atomically (no flicker, no 503 throttling).
        # Zozbieraj všetky zmeny a pošli ich v JEDNOM dávkovom requeste, aby sa
        # farba + jas + ON udiali naraz (žiadne blikanie, žiadne 503).
        pairs = []

        if ATTR_HS_COLOR in kwargs and self._hue_id and self._sat_id:
            hue, sat = kwargs[ATTR_HS_COLOR]
            pairs.append((self._hue_id, hue))
            pairs.append((self._sat_id, sat / 100.0))

        if ATTR_COLOR_TEMP_KELVIN in kwargs and self._cct_id:
            pairs.append((self._cct_id, kwargs[ATTR_COLOR_TEMP_KELVIN]))

        if ATTR_BRIGHTNESS in kwargs and self._brightness_id:
            brightness = kwargs[ATTR_BRIGHTNESS] / 255
            target_id = self._brightness_id
            if self._brightness_id == 42 and 67 in self.supported_val_ids:
                target_id = 67
            if self._brightness_id == 65 and 68 in self.supported_val_ids:
                target_id = 68
            pairs.append((target_id, brightness))

        # Only send ON if light isn't already on (avoids flicker on color-only changes).
        # This guard is critical — it is what fixed the button/light blinking issue.
        # Pošli ON iba ak svetlo nesvieti (predíde blikaniu pri samotnej zmene farby).
        # Tento guard je kľúčový — práve on vyriešil blikanie svetla pri tlačidlách.
        if not self.is_on:
            pairs.append((48, 1))

        if pairs:
            await self.coordinator.async_set_values(self.device_id, pairs)

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_value(self.device_id, 48, 0)
        await self.coordinator.async_request_refresh()
