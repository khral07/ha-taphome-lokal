import asyncio
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from . import DOMAIN
from .entity import TapHomeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices_config:
        supported_values = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        device_name_lower = device.get("name", "").lower()
        
        # 1. Klasické binárne senzory (ID 44 - Reed Contact / Senzor)
        if 44 in supported_values:
            device_class = None
            forced_icon = None

            # --- INTELIGENTNÁ DETEKCIA PODĽA NÁZVU ---
            if "brana" in device_name_lower or "brána" in device_name_lower or "gate" in device_name_lower:
                device_class = BinarySensorDeviceClass.GARAGE_DOOR # Správanie: Open/Closed
                forced_icon = "mdi:gate" # Vynútená ikona plotovej/posuvnej brány
            
            # 2. Garáž (Garage)
            elif "garaz" in device_name_lower or "garáž" in device_name_lower or "garage" in device_name_lower:
                device_class = BinarySensorDeviceClass.GARAGE_DOOR
            
            # 3. Pohyb (Motion)
            elif "pohyb" in device_name_lower or "motion" in device_name_lower:
                device_class = BinarySensorDeviceClass.MOTION

            # 4. Dvere (Door)
            elif "dvere" in device_name_lower or "door" in device_name_lower:
                device_class = BinarySensorDeviceClass.DOOR

            # 5. Okno (Window)
            elif "okno" in device_name_lower or "window" in device_name_lower:
                device_class = BinarySensorDeviceClass.WINDOW
            
            # Vytvorenie entity s parametrami
            entities.append(TapHomeBinarySensor(coordinator, device, 44, device_class, forced_icon))
            
    async_add_entities(entities)

class TapHomeBinarySensor(TapHomeEntity, BinarySensorEntity):
    """Klasický binárny senzor s možnosťou vlastnej ikony."""
    def __init__(self, coordinator, device_config, type_id, device_class, forced_icon=None):
        super().__init__(coordinator, device_config)
        self.type_id = type_id
        self._attr_unique_id = f"taphome_binary_{self.device_id}_{type_id}"
        self._attr_device_class = device_class
        
        # Ak sa vynútila ikonu (napr. pre bránu), nastavíme ju.
        # Ak nie, Home Assistant si ju vyberie sám podľa device_class.
        if forced_icon:
            self._attr_icon = forced_icon

    @property
    def is_on(self):
        val = self.coordinator.data.get(self.device_id, {}).get(self.type_id)
        return val == 1
