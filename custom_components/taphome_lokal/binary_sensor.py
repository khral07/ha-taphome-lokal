from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from . import DOMAIN
from .entity import TapHomeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices_config:
        supported = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        if 44 in supported:
            entities.append(TapHomeBinarySensor(coordinator, device, 44, BinarySensorDeviceClass.GARAGE_DOOR))
    async_add_entities(entities)

class TapHomeBinarySensor(TapHomeEntity, BinarySensorEntity):
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