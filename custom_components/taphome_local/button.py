from homeassistant.components.button import ButtonEntity
from . import DOMAIN
from .entity import TapHomeEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in coordinator.devices_config:
        supported_values = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        device_type = device.get("type", "")

        # Hľadáme tlačidlá:
        # 1. Majú ValueTypeId 52 (Push Button Action)
        # 2. Alebo sú explicitne typu "PushButton" / "VirtualPushButton"
        # 3. Alebo majú ValueTypeId 48 (Switch), ale nie sú to svetlá ani zásuvky, a chceme ich ako tlačidlo (voliteľné)
        # Pre istotu zariadenia, ktoré majú ID 52 (najčastejšie pre brány/tlačidlá)
        if 52 in supported_values:
            entities.append(TapHomeButton(coordinator, device))
        elif "PushButton" in device_type:
             entities.append(TapHomeButton(coordinator, device))

    async_add_entities(entities)

class TapHomeButton(TapHomeEntity, ButtonEntity):
    def __init__(self, coordinator, device_config):
        super().__init__(coordinator, device_config)
        self._attr_unique_id = f"taphome_button_{self.device_id}"

    async def async_press(self) -> None:
        """Spracuje stlačenie tlačidla."""
        # Pre tlačidlá zvyčajne hodnota 1 (stlačené) na ID 52
        # Ak zariadenie nemá 52, 48 (Switch) s hodnotou 1 (impulz)
        
        supported_values = [v['valueTypeId'] for v in self.device_config.get('supportedValues', [])]
        
        target_id = 52 # Default pre tlačidlo
        if 52 not in supported_values and 48 in supported_values:
            target_id = 48
            
        await self.coordinator.async_set_value(self.device_id, target_id, 1)
        # Tlačidlá nemajú stav, takže refresh nie je nutný, ale pre istotu ho môžeme zavolať
        await self.coordinator.async_request_refresh()
