from homeassistant.components.light import (
    LightEntity, 
    ColorMode, 
    ATTR_BRIGHTNESS, 
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_HS_COLOR  # <--- Zmena: Importujeme HS (Hue/Saturation) farbu
)
from . import DOMAIN
from .entity import TapHomeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices_config:
        supported_ids = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        
        has_brightness = (65 in supported_ids) or (42 in supported_ids)
        has_cct = (89 in supported_ids)
        has_color = (40 in supported_ids) and (41 in supported_ids) # <--- Zmena: Hľadáme ID 40 a 41
        is_lighting_category = device.get("category") == "OSVETLENIE"
        
        if has_brightness or has_cct or has_color or is_lighting_category:
            entities.append(TapHomeLight(coordinator, device))
    async_add_entities(entities)

class TapHomeLight(TapHomeEntity, LightEntity):
    def __init__(self, coordinator, device_config):
        super().__init__(coordinator, device_config)
        self._attr_unique_id = f"taphome_light_{self.device_id}"
        
        self.supported_val_ids = [v['valueTypeId'] for v in device_config.get('supportedValues', [])]
        
        # 1. Detekcia Jasu (ID 65 / 42)
        if 65 in self.supported_val_ids:
            self._brightness_id = 65
        elif 42 in self.supported_val_ids:
            self._brightness_id = 42
        else:
            self._brightness_id = None

        # 2. Detekcia Teploty farby (ID 89)
        self._cct_id = 89 if 89 in self.supported_val_ids else None
        
        # 3. Detekcia Farby (ID 40 - Hue, ID 41 - Saturation)
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
            if val: return int(val)
        return None

    # --- Čítanie HS farby z TapHome ---
    @property
    def hs_color(self):
        if self._hue_id and self._sat_id:
            hue = self._get_val(self._hue_id)
            sat = self._get_val(self._sat_id)
            if hue is not None and sat is not None:
                # HA používa sýtosť 0-100. Ak TapHome posiela 0.0 - 1.0 (ako pri jase), prenásobíme 100
                sat_ha = sat * 100 if sat <= 1.0 else sat
                return (hue, sat_ha)
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
        if self._hue_id and self._sat_id: modes.add(ColorMode.HS) # Podpora pre Odtieň/Sýtosť
        if self._cct_id: modes.add(ColorMode.COLOR_TEMP)
        if not modes and self._brightness_id: modes.add(ColorMode.BRIGHTNESS)
        if not modes: modes.add(ColorMode.ONOFF)
        return modes

    @property
    def color_mode(self):
        if self._hue_id and self._sat_id: return ColorMode.HS
        if self._cct_id: return ColorMode.COLOR_TEMP
        if self._brightness_id: return ColorMode.BRIGHTNESS
        return ColorMode.ONOFF

    def _get_val(self, type_id):
        data = self.coordinator.data or {}
        dev_data = data.get(self.device_id, {})
        return dev_data.get(type_id)

    async def async_turn_on(self, **kwargs):
        # 1. Nastavenie Farby (Hue/Saturation)
        if ATTR_HS_COLOR in kwargs and self._hue_id and self._sat_id:
            hue, sat = kwargs[ATTR_HS_COLOR]
            # Sýtosť z HA (0-100) prekonvertujeme pre TapHome (0.0-1.0)
            sat_taphome = sat / 100.0
            await self.coordinator.async_set_value(self.device_id, self._hue_id, hue)
            await self.coordinator.async_set_value(self.device_id, self._sat_id, sat_taphome)

        # 2. Nastavenie Teploty farby (CCT)
        if ATTR_COLOR_TEMP_KELVIN in kwargs and self._cct_id:
            kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]
            await self.coordinator.async_set_value(self.device_id, self._cct_id, kelvin)

        # 3. Nastavenie Jasu
        if ATTR_BRIGHTNESS in kwargs and self._brightness_id:
            brightness = kwargs[ATTR_BRIGHTNESS] / 255
            target_id = self._brightness_id
            if self._brightness_id == 42 and 67 in self.supported_val_ids: target_id = 67
            if self._brightness_id == 65 and 68 in self.supported_val_ids: target_id = 68
            await self.coordinator.async_set_value(self.device_id, target_id, brightness)
        
        # 4. Zapnutie
        await self.coordinator.async_set_value(self.device_id, 48, 1)
            
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_value(self.device_id, 48, 0)
        await self.coordinator.async_request_refresh()
