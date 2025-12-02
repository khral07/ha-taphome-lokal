from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from . import DOMAIN
from .entity import TapHomeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices_config:
        supported = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        if 1 in supported and device.get("category") != "OSVETLENIE":
            entities.append(TapHomeCover(coordinator, device))
    async_add_entities(entities)

class TapHomeCover(TapHomeEntity, CoverEntity):
    def __init__(self, coordinator, device_config):
        super().__init__(coordinator, device_config)
        self._attr_unique_id = f"taphome_cover_{self.device_id}"
        self._attr_supported_features = CoverEntityFeature.SET_POSITION | CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

    @property
    def current_cover_position(self):
        val = self.coordinator.data.get(self.device_id, {}).get(1)
        if val is not None: return int(val * 100)
        return 0

    @property
    def is_closed(self):
        return self.current_cover_position == 0

    async def async_open_cover(self, **kwargs):
        await self.coordinator.async_set_value(self.device_id, 1, 1.0)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs):
        await self.coordinator.async_set_value(self.device_id, 1, 0.0)
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs):
        pos = kwargs.get("position", 0) / 100.0
        await self.coordinator.async_set_value(self.device_id, 1, pos)
        await self.coordinator.async_request_refresh()