from homeassistant.components.select import SelectEntity
from . import DOMAIN
from .entity import TapHomeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices_config:
        for val in device.get("supportedValues", []):
            if val["valueTypeId"] == 49:
                entities.append(TapHomeSelect(coordinator, device, val))
    async_add_entities(entities)

class TapHomeSelect(TapHomeEntity, SelectEntity):
    def __init__(self, coordinator, device_config, value_config):
        super().__init__(coordinator, device_config)
        self._attr_unique_id = f"taphome_select_{self.device_id}"
        self.options_map = {item['name']: item['value'] for item in value_config.get('enumeratedValues', [])}
        self._attr_options = list(self.options_map.keys())

    @property
    def current_option(self):
        data = self.coordinator.data.get(self.device_id, {})
        val = data.get(49)
        for name, value in self.options_map.items():
            if value == int(val or 0): return name
        return None

    async def async_select_option(self, option: str):
        val_to_send = self.options_map.get(option)
        if val_to_send is not None:
            await self.coordinator.async_set_value(self.device_id, 71, val_to_send)
            await self.coordinator.async_request_refresh()