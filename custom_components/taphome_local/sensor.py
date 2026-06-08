import math
import re
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfTemperature, PERCENTAGE, LIGHT_LUX, UnitOfPower, UnitOfEnergy
from . import DOMAIN
from .entity import TapHomeEntity

# Map common bracketed units in TapHome device names to HA device classes.
# Mapovanie bežných jednotiek v názve zariadenia na HA device_class.
_UNIT_DEVICE_CLASS = {
    "kwh": SensorDeviceClass.ENERGY,
    "wh": SensorDeviceClass.ENERGY,
    "w": SensorDeviceClass.POWER,
    "kw": SensorDeviceClass.POWER,
    "v": SensorDeviceClass.VOLTAGE,
    "a": SensorDeviceClass.CURRENT,
    "°c": SensorDeviceClass.TEMPERATURE,
    "%": SensorDeviceClass.HUMIDITY,
}


def _parse_name_unit(name):
    """Extract trailing [unit] from a device name. / Vytiahne koncovú [jednotku] z názvu.

    Returns (clean_name, unit, device_class). Unit/class are None if absent.
    """
    m = re.search(r"\[([^\]]+)\]\s*$", name or "")
    if not m:
        return name, None, None
    unit = m.group(1).strip()
    clean = name[: m.start()].strip()
    dclass = _UNIT_DEVICE_CLASS.get(unit.lower())
    return (clean or name), unit, dclass


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
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
        supported = {v["valueTypeId"] for v in device.get("supportedValues", [])}

        for val in device.get("supportedValues", []):
            tid = val["valueTypeId"]
            if tid in SENSOR_TYPES:
                cls, unit, suffix = SENSOR_TYPES[tid]
                entities.append(TapHomeSensor(coordinator, device, tid, suffix, cls, unit))

        # VariableState (62): generic numeric value (Modbus variables, energy meters...).
        # Generická číselná hodnota — názov často obsahuje [jednotku].
        if 62 in supported:
            clean, unit, dclass = _parse_name_unit(device.get("name", ""))
            state_class = "total_increasing" if dclass == SensorDeviceClass.ENERGY else "measurement"
            entities.append(
                TapHomeSensor(coordinator, device, 62, None, dclass, unit, state_class=state_class)
            )

    async_add_entities(entities)

class TapHomeSensor(TapHomeEntity, SensorEntity):
    def __init__(self, coordinator, device_config, type_id, suffix, device_class, unit, state_class=None):
        super().__init__(coordinator, device_config)
        self.type_id = type_id
        # has_entity_name=True prepends the device name automatically, so the entity name is
        # just the suffix -> friendly name "<device> <suffix>" (same as before). If suffix is
        # None, the sensor IS the device's main value and keeps just the device name.
        # has_entity_name=True automaticky pridá názov zariadenia, takže názov entity je len
        # suffix -> friendly name "<zariadenie> <suffix>" (ako doteraz). Ak je suffix None,
        # senzor je hlavná hodnota zariadenia a ponechá len názov zariadenia.
        if suffix:
            self._attr_name = suffix
        self._attr_unique_id = f"taphome_sensor_{self.device_id}_{type_id}"
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        if state_class:
            self._attr_state_class = state_class

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
                return round(float_val * 100, 1)

            return float_val
        except (ValueError, TypeError):
            return None

    @property
    def available(self):
        return self.coordinator.last_update_success