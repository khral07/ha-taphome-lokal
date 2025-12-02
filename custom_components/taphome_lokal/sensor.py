import math
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfTemperature, PERCENTAGE, LIGHT_LUX, UnitOfPower, UnitOfEnergy
from . import DOMAIN
from .entity import TapHomeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    
    SENSOR_TYPES = {
        5: (SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS, "Temperature"),
        3: (SensorDeviceClass.HUMIDITY, PERCENTAGE, "Humidity"),
        24: (SensorDeviceClass.ILLUMINANCE, LIGHT_LUX, "Brightness"),
        4: (SensorDeviceClass.CO2, "ppm", "CO2"),
        77: (SensorDeviceClass.POWER, UnitOfPower.WATT, "Power"),
        75: (SensorDeviceClass.ENERGY, UnitOfEnergy.KILO_WATT_HOUR, "Energy"),
        15: (None, "m/s", "Wind Speed"),
        21: (None, None, "Active Sensors"),
    }

    for device in coordinator.devices_config:
        for val in device.get("supportedValues", []):
            tid = val["valueTypeId"]
            if tid in SENSOR_TYPES:
                cls, unit, suffix = SENSOR_TYPES[tid]
                entities.append(TapHomeSensor(coordinator, device, tid, suffix, cls, unit))

    async_add_entities(entities)

class TapHomeSensor(TapHomeEntity, SensorEntity):
    def __init__(self, coordinator, device_config, type_id, suffix, device_class, unit):
        super().__init__(coordinator, device_config)
        self.type_id = type_id
        self._attr_name = f"{device_config['name']} {suffix}"
        self._attr_unique_id = f"taphome_sensor_{self.device_id}_{type_id}"
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        dev_data = data.get(self.device_id, {})
        raw_val = dev_data.get(self.type_id)

        if raw_val is None: return None

        try:
            float_val = float(raw_val)
            if math.isnan(float_val) or math.isinf(float_val):
                return None
            
            # --- FIX FOR HUMIDITY / FIX PRE VLHKOSŤ ---
            # If humidity (3), TapHome sends 0.47, we want 47 / Ak je to vlhkosť (3), TapHome posiela 0.47, my chceme 47
            if self.type_id == 3:
                return int(float_val * 100)
            
            return float_val
        except (ValueError, TypeError):
            return None

    @property
    def available(self):
        return self.coordinator.last_update_success