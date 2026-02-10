import math
from datetime import datetime
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import UnitOfTemperature, PERCENTAGE, LIGHT_LUX, UnitOfPower, UnitOfEnergy
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from . import DOMAIN, SIGNAL_BUTTON_PRESSED
from .entity import TapHomeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    
    # Definícia bežných senzorov
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
        supported = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        
        # 1. Štandardné senzory (Teplota, Vlhkosť...)
        for val in supported:
            if val in SENSOR_TYPES:
                cls, unit, suffix = SENSOR_TYPES[val]
                entities.append(TapHomeSensor(coordinator, device, val, suffix, cls, unit))
        
        # 2. Push Button ako TIMESTAMP Senzor (ID 52)
        # Toto rieši ten problém s dotykovým tlačidlom - bude ukazovať čas posledného stlačenia
        if 52 in supported:
             entities.append(TapHomeTimestampSensor(coordinator, device))

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
            
            # FIX PRE VLHKOSŤ: TapHome posiela 0.47, my chceme 47 %
            if self.type_id == 3:
                return int(float_val * 100)
                
            return float_val
        except:
            return raw_val

class TapHomeTimestampSensor(TapHomeEntity, SensorEntity):
    """Senzor, ktorý ukazuje čas posledného stlačenia tlačidla."""
    
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, coordinator, device_config):
        super().__init__(coordinator, device_config)
        # ID 52 je fixné pre Push Button Action
        self._attr_unique_id = f"taphome_last_press_{self.device_id}"
        self._attr_name = f"{device_config['name']} Last Press"
        self._last_press = None

    async def async_added_to_hass(self):
        """Počúvame na Webhook signál."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_BUTTON_PRESSED.format(self.device_id),
                self._handle_button_press
            )
        )

    @callback
    def _handle_button_press(self):
        """Keď príde webhook, aktualizujeme čas na aktuálny."""
        self._last_press = datetime.now()
        self.async_write_ha_state()

    @property
    def native_value(self):
        return self._last_press