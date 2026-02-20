from homeassistant.components.switch import SwitchEntity
from . import DOMAIN
from .entity import TapHomeEntity
from .const import (
    CONF_EXPOSE_AS_LIGHT, 
    CONF_EXPOSE_AS_VALVE, 
    CONF_EXPOSE_AS_COVER  
)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Načítame zoznamy zariadení, ktoré užívateľ manuálne zmenil na iný typ
    forced_lights = entry.options.get(CONF_EXPOSE_AS_LIGHT, [])
    forced_valves = entry.options.get(CONF_EXPOSE_AS_VALVE, [])
    forced_covers = entry.options.get(CONF_EXPOSE_AS_COVER, []) 

    entities = []
    for device in coordinator.devices_config:
        # Pre istotu prevedieme ID na string (pre porovnávanie so zoznamom)
        dev_id = str(device["deviceId"])
        supported = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        
        # --- 1. KROK: FILTRÁCIA MANUÁLNYCH VÝBEROV ---
        # Ak užívateľ povedal, že toto je SVETLO, VENTIL alebo BRÁNA, 
        # tak tu okamžite končíme a nevytvárame Switch.
        if (dev_id in forced_lights) or (dev_id in forced_valves) or (dev_id in forced_covers):
            continue
        
        # --- 2. KROK: AUTOMATICKÁ FILTRÁCIA (pôvodná logika) ---
        if (48 in supported 
            and 65 not in supported  # Jas
            and 42 not in supported  # Analógový výstup / Jas
            and 40 not in supported  # Hue (Odtieň farby)
            and 41 not in supported  # Saturation (Sýtosť)
            and 70 not in supported  # RGBW (Farba)
            and 89 not in supported  # CCT (Teplota farby)
            and 1 not in supported   # Žalúzie (Level)
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
