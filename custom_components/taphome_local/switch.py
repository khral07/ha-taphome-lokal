from homeassistant.components.switch import SwitchEntity
from . import DOMAIN
from .entity import TapHomeEntity
from .const import (
    CONF_EXPOSE_AS_LIGHT,
    CONF_EXPOSE_AS_VALVE,
    CONF_EXPOSE_AS_COVER,
    CONF_EXPOSE_AS_SWITCH,
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    forced_lights = entry.options.get(CONF_EXPOSE_AS_LIGHT, [])
    forced_valves = entry.options.get(CONF_EXPOSE_AS_VALVE, [])
    forced_covers = entry.options.get(CONF_EXPOSE_AS_COVER, [])
    forced_switches = entry.options.get(CONF_EXPOSE_AS_SWITCH, [])

    entities = []
    seen = set()
    for device in coordinator.devices_config:
        dev_id = str(device["deviceId"])
        supported = [v['valueTypeId'] for v in device.get('supportedValues', [])]

        # If user forced this to another platform, skip. / Ak je forced inam, preskočiť.
        if (dev_id in forced_lights) or (dev_id in forced_valves) or (dev_id in forced_covers):
            continue

        # Explicit force as switch (needs SwitchState ID 48). / Vynútený switch.
        if dev_id in forced_switches and 48 in supported:
            if dev_id not in seen:
                entities.append(TapHomeSwitch(coordinator, device))
                seen.add(dev_id)
            continue

        # Auto-detection: plain relay, not a light/cover. / Auto-detekcia relé.
        if (48 in supported
            and 65 not in supported
            and 42 not in supported
            and 40 not in supported
            and 41 not in supported
            and 70 not in supported
            and 89 not in supported
            and 1 not in supported
            and device.get("category") != "OSVETLENIE"):

            if dev_id not in seen:
                entities.append(TapHomeSwitch(coordinator, device))
                seen.add(dev_id)

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
