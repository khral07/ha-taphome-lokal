from homeassistant.components.switch import SwitchEntity
from . import DOMAIN
from .entity import TapHomeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices_config:
        supported = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        
        # LOGIKA FILTRÁCIE pre Switch:
        if (48 in supported 
            and 65 not in supported  # Jas
            and 42 not in supported  # Analógový výstup / Jas
            and 40 not in supported  # Hue (Odtieň farby) - PRIDANÉ
            and 41 not in supported  # Saturation (Sýtosť) - PRIDANÉ
            and 70 not in supported  # RGBW (Farba) - PRIDANÉ
            and 89 not in supported  # CCT (Teplota farby) - PRIDANÉ
            and 1 not in supported   # Žalúzie
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
