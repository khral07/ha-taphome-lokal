import asyncio
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.core import callback
# IMPORT PRE PRÍJEM SIGNÁLU
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from . import DOMAIN, SIGNAL_BUTTON_PRESSED
from .entity import TapHomeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices_config:
        supported_values = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        
        # 1. Classic sensors
        if 44 in supported_values:
            entities.append(TapHomeBinarySensor(coordinator, device, 44, BinarySensorDeviceClass.GARAGE_DOOR))
            
        # 2. Push Buttons - ID 52
        # Poznámka: Pre tento nový systém podporujeme primárne ID 52 (ktoré posiela váš webhook)
        if 52 in supported_values:
            entities.append(TapHomePushButtonSensor(coordinator, device))

    async_add_entities(entities)

class TapHomeBinarySensor(TapHomeEntity, BinarySensorEntity):
    """Klasický binárny senzor (Dvere/Okná)."""
    def __init__(self, coordinator, device_config, type_id, device_class):
        super().__init__(coordinator, device_config)
        self.type_id = type_id
        self._attr_unique_id = f"taphome_binary_{self.device_id}_{type_id}"
        self._attr_device_class = device_class

    @property
    def is_on(self):
        data = self.coordinator.data.get(self.device_id, {})
        val = data.get(self.type_id)
        return bool(val)

class TapHomePushButtonSensor(TapHomeEntity, BinarySensorEntity):
    """Senzor pre fyzické tlačidlo reagujúci na SIGNÁL."""
    def __init__(self, coordinator, device_config):
        super().__init__(coordinator, device_config)
        # ID 52 je hardcoded, lebo tento senzor reaguje len naň
        self._attr_unique_id = f"taphome_push_sensor_{self.device_id}_52"
        self._attr_icon = "mdi:gesture-tap-button"
        self._attr_name = f"{device_config['name']} Button"
        
        self._is_pressed = False
        self._off_task = None

    @property
    def is_on(self):
        return self._is_pressed

    async def async_added_to_hass(self):
        """Namiesto koordinátora počúvame špecifický SIGNÁL pre toto ID."""
        await super().async_added_to_hass()
        
        # Prihlásime sa na odber signálu: taphome_button_pressed_25 (napr.)
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_BUTTON_PRESSED.format(self.device_id),
                self._handle_button_press
            )
        )

    @callback
    def _handle_button_press(self):
        """Táto funkcia sa spustí LEN vtedy, keď príde nový webhook s ID 52."""
        # Ak už beží vypínanie, zrušíme ho
        if self._off_task:
            self._off_task.cancel()
        
        # Zapneme
        self._is_pressed = True
        self.async_write_ha_state() 
        
        # Naplánujeme vypnutie
        self._off_task = self.hass.loop.create_task(self._auto_turn_off())

    async def _auto_turn_off(self):
        """Počká a vypne."""
        await asyncio.sleep(0.3)
        self._is_pressed = False
        self.async_write_ha_state()