import asyncio
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from . import DOMAIN
from .entity import TapHomeEntity
from .const import SIGNAL_BUTTON_PRESSED

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
            
        # --- CHÝBAJÚCA ČASŤ: Tlačidlá (ID 52) ako impulzné binárne senzory ---
        if 52 in supported_values:
            entities.append(TapHomePushButton(coordinator, device))

    async_add_entities(entities)

class TapHomeBinarySensor(TapHomeEntity, BinarySensorEntity):
    """Klasický binárny senzor s možnosťou vlastnej ikony."""
    def __init__(self, coordinator, device_config, type_id, device_class, forced_icon=None):
        super().__init__(coordinator, device_config)
        self.type_id = type_id
        self._attr_unique_id = f"taphome_binary_{self.device_id}_{type_id}"
        self._attr_device_class = device_class
        
        # Ak sa vynútila ikonu (napr. pre bránu), nastavíme ju.
        if forced_icon:
            self._attr_icon = forced_icon

    @property
    def is_on(self):
        val = self.coordinator.data.get(self.device_id, {}).get(self.type_id)
        return val == 1


class TapHomePushButton(TapHomeEntity, BinarySensorEntity):
    """Impulzný binárny senzor pre fyzické tlačidlo (reaguje na webhook impulz)."""
    def __init__(self, coordinator, device_config):
        super().__init__(coordinator, device_config)
        self._attr_unique_id = f"taphome_pushbutton_{self.device_id}"
        self._attr_icon = "mdi:gesture-tap-button"
        self._is_on = False

    @property
    def is_on(self):
        return self._is_on

    async def async_added_to_hass(self):
        """Keď je entita pridaná, začne počúvať signál stlačenia z Webhooku."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, 
                SIGNAL_BUTTON_PRESSED.format(self.device_id), 
                self._handle_button_press
            )
        )

    async def _handle_button_press(self):
        """Simuluje krátky impulz (0.3s) po prijatí signálu."""
        self._is_on = True
        self.async_write_ha_state()
        
        # Počkáme 0.3 sekundy a vrátime stav na vypnuté
        await asyncio.sleep(0.3)
        
        self._is_on = False
        self.async_write_ha_state()
