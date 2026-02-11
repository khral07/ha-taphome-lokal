from homeassistant.components.switch import SwitchEntity
from . import DOMAIN
from .entity import TapHomeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices_config:
        supported = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        
        # LOGIKA FILTRÁCIE:
        # Vytvoríme prepínač (Switch) len ak:
        # 1. Má atribút 48 (Relé/Switch)
        # 2. NEMÁ atribút 65 (Jas - to patrí do light.py)
        # 3. NEMÁ atribút 42 (Analógový výstup/Jas - to tiež patrí do light.py)
        # 4. NEMÁ atribút 1 (Žalúzie - to patrí do cover.py)
        # 5. Kategória NIE JE "OSVETLENIE" (to rieši light.py, aj keď je to obyčajné relé)
        
        if (48 in supported 
            and 65 not in supported 
            and 42 not in supported
            and 1 not in supported 
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