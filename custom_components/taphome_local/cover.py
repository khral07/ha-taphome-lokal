from homeassistant.components.cover import (
    CoverEntity, 
    CoverEntityFeature, 
    CoverDeviceClass
)
from . import DOMAIN
from .entity import TapHomeEntity
from .const import CONF_EXPOSE_AS_COVER

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Načítame zoznam manuálne vybratých brán
    forced_covers = entry.options.get(CONF_EXPOSE_AS_COVER, [])

    entities = []
    for device in coordinator.devices_config:
        dev_id = str(device["deviceId"])
        supported = [v['valueTypeId'] for v in device.get('supportedValues', [])]
        
        # 1. KLASICKÉ ŽALÚZIE (ID 1 - Level)
        if 1 in supported and device.get("category") != "OSVETLENIE":
            entities.append(TapHomeCover(coordinator, device))
        
        # 2. BRÁNY (Manuálne vybraté)
        elif dev_id in forced_covers:
            # A) Je to RELÉ (ID 48) - vieme stav ON/OFF
            if 48 in supported:
                entities.append(TapHomeDoorCover(coordinator, device, control_id=48))
            # B) Je to TLAČIDLO (ID 52) - Tvoj prípad (len impulz)
            elif 52 in supported:
                entities.append(TapHomeDoorCover(coordinator, device, control_id=52))
            
    async_add_entities(entities)

# --- TRIEDA 1: ŽALÚZIE (Polohovateľné) ---
class TapHomeCover(TapHomeEntity, CoverEntity):
    def __init__(self, coordinator, device_config):
        super().__init__(coordinator, device_config)
        self._attr_unique_id = f"taphome_cover_{self.device_id}"
        self._attr_device_class = CoverDeviceClass.BLIND 
        self._attr_supported_features = (
            CoverEntityFeature.SET_POSITION | 
            CoverEntityFeature.OPEN | 
            CoverEntityFeature.CLOSE
        )

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


# --- TRIEDA 2: BRÁNY (Relé alebo Tlačidlo) ---
class TapHomeDoorCover(TapHomeEntity, CoverEntity):
    def __init__(self, coordinator, device_config, control_id):
        super().__init__(coordinator, device_config)
        self._control_id = control_id # Zapamätáme si, či ovládame 48 alebo 52
        self._attr_unique_id = f"taphome_gate_{self.device_id}"
        self._attr_device_class = CoverDeviceClass.GARAGE
        self._attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

    @property
    def is_closed(self):
        # Ak je to Relé (48), vieme zistiť, či je brána zatvorená (0) alebo otvorená (1)
        if self._control_id == 48:
            val = self.coordinator.data.get(self.device_id, {}).get(48)
            return val == 0 if val is not None else None
        
        # Ak je to Tlačidlo (52), NEVIEME zistiť stav. 
        # Brána sa len "prepne". V HA bude stav "Neznámy" alebo len ikona, čo je OK.
        return None 

    async def async_open_cover(self, **kwargs):
        # Ak je to tlačidlo (52), pošleme impulz (True/1)
        target_val = 1
        await self.coordinator.async_set_value(self.device_id, self._control_id, target_val)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs):
        # Pri tlačidle (52) aj príkaz "Zatvoriť" znamená "Stlačiť tlačidlo"
        target_val = 1 if self._control_id == 52 else 0
        await self.coordinator.async_set_value(self.device_id, self._control_id, target_val)
        await self.coordinator.async_request_refresh()
