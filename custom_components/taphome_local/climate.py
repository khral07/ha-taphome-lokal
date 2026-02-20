import math
from homeassistant.components.climate import ClimateEntity, HVACMode, ClimateEntityFeature
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE
from . import DOMAIN
from .entity import TapHomeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices_config:
        supported_values = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        if 6 in supported_values:
            entities.append(TapHomeClimate(coordinator, device))
    async_add_entities(entities)

class TapHomeClimate(TapHomeEntity, ClimateEntity):
    def __init__(self, coordinator, device_config):
        super().__init__(coordinator, device_config)
        self._attr_unique_id = f"taphome_climate_{self.device_id}"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        
        # Thermostat is usually always in HEAT mode / Termostat je zvyčajne stále v režime KÚRENIE
        self._attr_hvac_modes = [HVACMode.HEAT]
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        
        # Load limits for slider / Načítanie limitov pre posuvník
        self._attr_min_temp = 15
        self._attr_max_temp = 25
        
        for val in device_config.get("supportedValues", []):
            if val["valueTypeId"] == 6: # SetPoint
                if "minValue" in val:
                    self._attr_min_temp = val["minValue"]
                if "maxValue" in val:
                    self._attr_max_temp = val["maxValue"]
                break

    @property
    def current_temperature(self):
        # Current temperature (ID 5) / Aktuálna teplota (ID 5).
        val = self._get_val(5)
        return self._safe_float(val)

    @property
    def target_temperature(self):
        # Target temperature (ID 6) / Nastavená teplota (ID 6).
        val = self._get_val(6)
        return self._safe_float(val)

    @property
    def hvac_mode(self):
        return HVACMode.HEAT

    def _get_val(self, type_id):
        data = self.coordinator.data or {}
        dev_data = data.get(self.device_id, {})
        return dev_data.get(type_id)
        
    def _safe_float(self, val):
        # Protection against 'nan' errors / Ochrana proti 'nan' chybám.
        if val is None: return None
        try:
            f = float(val)
            if math.isnan(f) or math.isinf(f): return None
            return f
        except: return None

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp:
            await self.coordinator.async_set_value(self.device_id, 6, temp)
            await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode):
        pass
