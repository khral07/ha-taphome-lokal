from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity, 
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState 
)
from . import DOMAIN
from .entity import TapHomeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices_config:
        supported_values = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        if 19 in supported_values and 20 in supported_values:
            entities.append(TapHomeAlarm(coordinator, device))
    async_add_entities(entities)

class TapHomeAlarm(TapHomeEntity, AlarmControlPanelEntity):
    def __init__(self, coordinator, device_config):
        super().__init__(coordinator, device_config)
        self._attr_unique_id = f"taphome_alarm_{self.device_id}"
        self._attr_supported_features = AlarmControlPanelEntityFeature.ARM_HOME | AlarmControlPanelEntityFeature.ARM_AWAY

    @property
    def alarm_state(self):
        data = self.coordinator.data.get(self.device_id, {})
        # AlarmState (20): 0=OK, 1=Warning, 2=Alarm / AlarmState (20): 0=OK, 1=Varovanie, 2=Alarm
        state_val = data.get(20, 0)
        
        if state_val == 2:
            return AlarmControlPanelState.TRIGGERED
            
        # AlarmMode (19): 0=Home (Disarmed), 1=Away (Armed) / AlarmMode (19): 0=Doma (Deaktivované), 1=Preč (Aktivované)
        mode_val = data.get(19, 0)
        if mode_val == 1:
            return AlarmControlPanelState.ARMED_AWAY
        elif mode_val == 0:
            return AlarmControlPanelState.DISARMED
        
        return AlarmControlPanelState.DISARMED

    async def async_alarm_disarm(self, code=None):
        await self.coordinator.async_set_value(self.device_id, 19, 0) # Home
        await self.coordinator.async_request_refresh()

    async def async_alarm_arm_home(self, code=None):
        await self.coordinator.async_set_value(self.device_id, 19, 0) # Home
        await self.coordinator.async_request_refresh()

    async def async_alarm_arm_away(self, code=None):
        await self.coordinator.async_set_value(self.device_id, 19, 1) # Away
        await self.coordinator.async_request_refresh()