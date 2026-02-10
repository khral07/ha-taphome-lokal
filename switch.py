from homeassistant.components.switch import SwitchEntity
from . import DOMAIN
from .entity import TapHomeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices_config:
        supported = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        
        # Podmienky pre vytvorenie prepínača (Switch):
        # 1. Musí mať atribút 48 (Switch/Relé)
        # 2. Nesmie mať atribút 65 (Stmievanie - inak je to svetlo)
        # 3. Nesmie mať atribút 1 (Žalúzie - inak je to cover)
        # 4. Nesmie mať atribút 52 (Push Button - to sme presunuli do sensor.py ako Timestamp)
        # 5. Kategória nesmie byť "OSVETLENIE" (aby sa neduplikovalo so svetlami)
        
        if (48 in supported 
            and 65 not in supported 
            and 1 not in supported 
            and 52 not in supported 
            and device.get("category") != "OSVETLENIE"):
            
            entities.append(TapHomeSwitch(coordinator, device))
            
    async_add_entities(entities)

class TapHomeSwitch(TapHomeEntity, SwitchEntity):
    def __init__(self, coordinator, device_config):
        super().__init__(coordinator, device_config)
        self._attr_unique_id = f"taphome_switch_{self.device_id}"

    @property
    def is_on(self):
        val = self.coordinator.data.get(self.device_id, {}).get(48)
        return val == 1

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_value(self.device_id, 48, 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_value(self.device_id, 48, 0)
        await self.coordinator.async_request_refresh()