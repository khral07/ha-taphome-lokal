from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS, ATTR_COLOR_TEMP_KELVIN
from . import DOMAIN
from .entity import TapHomeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices_config:
        supported_ids = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        
        # Is it a light? Has Brightness (65/42), CCT (89) or category LIGHTING / Je to svetlo? Má Jas (65/42), CCT (89) alebo kategóriu OSVETLENIE
        has_brightness = (65 in supported_ids) or (42 in supported_ids)
        has_cct = (89 in supported_ids)
        is_lighting_category = device.get("category") == "OSVETLENIE"
        
        if has_brightness or has_cct or is_lighting_category:
            entities.append(TapHomeLight(coordinator, device))
    async_add_entities(entities)

class TapHomeLight(TapHomeEntity, LightEntity):
    def __init__(self, coordinator, device_config):
        super().__init__(coordinator, device_config)
        self._attr_unique_id = f"taphome_light_{self.device_id}"
        
        self.supported_val_ids = [v['valueTypeId'] for v in device_config.get('supportedValues', [])]
        
        # 1. Brightness detection / 1. Detekcia Jasu
        if 65 in self.supported_val_ids:
            self._brightness_id = 65
        elif 42 in self.supported_val_ids:
            self._brightness_id = 42
        else:
            self._brightness_id = None

        # 2. Color Temperature detection / 2. Detekcia Teploty farby
        self._cct_id = 89 if 89 in self.supported_val_ids else None
        
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
        # Fallback: if switch state missing, check brightness > 0 / Fallback: ak chýba stav vypínača, skontrolujeme jas > 0
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
            if val: return int(val)
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
        if self._cct_id: modes.add(ColorMode.COLOR_TEMP)
        elif self._brightness_id: modes.add(ColorMode.BRIGHTNESS)
        else: modes.add(ColorMode.ONOFF)
        return modes

    @property
    def color_mode(self):
        if self._cct_id: return ColorMode.COLOR_TEMP
        if self._brightness_id: return ColorMode.BRIGHTNESS
        return ColorMode.ONOFF

    def _get_val(self, type_id):
        data = self.coordinator.data or {}
        dev_data = data.get(self.device_id, {})
        return dev_data.get(type_id)

    async def async_turn_on(self, **kwargs):
        # 1. Set Color Temperature / 1. Nastavenie teploty farby
        if ATTR_COLOR_TEMP_KELVIN in kwargs and self._cct_id:
            kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]
            await self.coordinator.async_set_value(self.device_id, self._cct_id, kelvin)

        # 2. Set Brightness / 2. Nastavenie jasu
        if ATTR_BRIGHTNESS in kwargs and self._brightness_id:
            brightness = kwargs[ATTR_BRIGHTNESS] / 255
            target_id = self._brightness_id
            if self._brightness_id == 42 and 67 in self.supported_val_ids: target_id = 67
            if self._brightness_id == 65 and 68 in self.supported_val_ids: target_id = 68
            await self.coordinator.async_set_value(self.device_id, target_id, brightness)
        
        # 3. Always turn on switch (Move to On behavior) / 3. VŽDY pošleme príkaz na zapnutie (správanie Move to On)
        await self.coordinator.async_set_value(self.device_id, 48, 1)
            
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_value(self.device_id, 48, 0)
        await self.coordinator.async_request_refresh()