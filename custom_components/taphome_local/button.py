import homeassistant.util.dt as dt_util
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from . import DOMAIN
from .entity import TapHomeEntity
from .const import SIGNAL_BUTTON_PRESSED

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices_config:
        supported_values = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        device_type = device.get("type", "")

        # Ak je to ID 52 alebo PushButton, vytvoríme preň tlačidlo
        if 52 in supported_values or "PushButton" in device_type:
            entities.append(TapHomeButton(coordinator, device))

    async_add_entities(entities)

class TapHomeButton(TapHomeEntity, ButtonEntity):
    def __init__(self, coordinator, device_config):
        super().__init__(coordinator, device_config)
        self._attr_unique_id = f"taphome_button_{self.device_id}"

    async def async_added_to_hass(self):
        """Po štarte začne počúvať signál stlačenia z Webhooku."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, 
                SIGNAL_BUTTON_PRESSED.format(self.device_id), 
                self._handle_physical_press
            )
        )

    async def _handle_physical_press(self):
        """Zaznamená fyzické stlačenie na stene a posunie ho do HA."""
        # Aktualizujeme stav tlačidla na aktuálny čas. 
        # Toto zabezpečí, že HA to zaregistruje ako stlačenie a spustí automatizácie.
        self._attr_state = dt_util.utcnow().isoformat()
        self.async_write_ha_state()

    async def async_press(self) -> None:
        """Odošle príkaz na stlačenie do TapHome, keď klikneš v HA aplikácii."""
        supported_values = [v['valueTypeId'] for v in self.device_config.get('supportedValues', [])]
        target_id = 52
        if 52 not in supported_values and 48 in supported_values:
            target_id = 48
            
        await self.coordinator.async_set_value(self.device_id, target_id, 1)
        await self.coordinator.async_request_refresh()
