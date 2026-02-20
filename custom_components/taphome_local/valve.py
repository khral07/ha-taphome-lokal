from homeassistant.components.valve import ValveEntity, ValveEntityFeature, ValveDeviceClass
from . import DOMAIN
from .entity import TapHomeEntity
from .const import CONF_EXPOSE_AS_VALVE

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Načítame manuálne vynútené ventily
    forced_valves = entry.options.get(CONF_EXPOSE_AS_VALVE, [])

    entities = []
    for device in coordinator.devices_config:
        dev_id = str(device["deviceId"])
        supported = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        
        # LOGIKA: Pridáme len ak to užívateľ explicitne vybral v menu
        if (dev_id in forced_valves) and (48 in supported):
             entities.append(TapHomeValve(coordinator, device))
            
    async_add_entities(entities)

class TapHomeValve(TapHomeEntity, ValveEntity):
    def __init__(self, coordinator, device_config):
        super().__init__(coordinator, device_config)
        self._attr_unique_id = f"taphome_valve_{self.device_id}"
        self._attr_device_class = ValveDeviceClass.WATER
        self._attr_supported_features = ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE

    @property
    def is_closed(self):
        val = self.coordinator.data.get(self.device_id, {}).get(48)
        return val == 0 if val is not None else None

    async def async_open_valve(self, **kwargs):
        await self.coordinator.async_set_value(self.device_id, 48, 1)
        await self.coordinator.async_request_refresh()

    async def async_close_valve(self, **kwargs):
        await self.coordinator.async_set_value(self.device_id, 48, 0)
        await self.coordinator.async_request_refresh()
