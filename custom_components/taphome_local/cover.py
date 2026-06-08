from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
    CoverDeviceClass
)
from . import DOMAIN
from .entity import TapHomeEntity
from .const import CONF_EXPOSE_AS_COVER

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data

    # Načítame zoznam manuálne vybratých brán
    forced_covers = entry.options.get(CONF_EXPOSE_AS_COVER, [])

    entities = []
    for device in coordinator.devices_config:
        dev_id = str(device["deviceId"])
        supported = [v['valueTypeId'] for v in device.get('supportedValues', [])]

        # 1. KLASICKÉ ŽALÚZIE — ID 46 (BlindsLevel / VirtualBlindGroup) alebo ID 1 (Level)
        if (1 in supported or 46 in supported) and device.get("category") != "OSVETLENIE":
            entities.append(TapHomeCover(coordinator, device))

        # 2. BRÁNY (Manuálne vybraté)
        elif dev_id in forced_covers:
            # A) Relé (ID 48) — vieme stav ON/OFF
            if 48 in supported:
                entities.append(TapHomeDoorCover(coordinator, device, control_id=48))
            # B) Tlačidlo (ID 52) — len impulz
            elif 52 in supported:
                entities.append(TapHomeDoorCover(coordinator, device, control_id=52))

    async_add_entities(entities)


# --- TRIEDA 1: ŽALÚZIE (Polohovateľné, voliteľne s lamelami) ---
class TapHomeCover(TapHomeEntity, CoverEntity):
    def __init__(self, coordinator, device_config):
        super().__init__(coordinator, device_config)
        self._attr_unique_id = f"taphome_cover_{self.device_id}"
        self._attr_device_class = CoverDeviceClass.BLIND

        supported = [v['valueTypeId'] for v in device_config.get('supportedValues', [])]

        # Prefer ID 46 (BlindsLevel — VirtualBlindGroup), fallback na ID 1 (Level)
        self._pos_id = 46 if 46 in supported else 1
        self._has_tilt = 10 in supported  # BlindsSlope — uhol lamiel
        self._has_moving = 66 in supported  # BlindsIsMoving (read-only)
        self._last_cmd = None  # "open" | "close" | None — posledný smer príkazu

        features = (
            CoverEntityFeature.SET_POSITION |
            CoverEntityFeature.OPEN |
            CoverEntityFeature.CLOSE |
            CoverEntityFeature.STOP
        )
        if self._has_tilt:
            features |= (
                CoverEntityFeature.SET_TILT_POSITION |
                CoverEntityFeature.OPEN_TILT |
                CoverEntityFeature.CLOSE_TILT
            )
        self._attr_supported_features = features

    @property
    def current_cover_position(self):
        val = self.coordinator.data.get(self.device_id, {}).get(self._pos_id)
        if val is not None:
            # TapHome: 0.0 = open, 1.0 = closed — invertujeme pre HA (0 = closed, 100 = open)
            return int((1.0 - val) * 100)
        return None

    @property
    def current_cover_tilt_position(self):
        if not self._has_tilt:
            return None
        val = self.coordinator.data.get(self.device_id, {}).get(10)
        if val is not None:
            return int((1.0 - val) * 100)
        return None

    @property
    def is_closed(self):
        pos = self.current_cover_position
        if pos is None:
            return None
        return pos == 0

    @property
    def _is_moving(self):
        # BlindsIsMoving (66): True kým sa žalúzia hýbe. / True while the blind is moving.
        if not self._has_moving:
            return False
        return bool(self.coordinator.data.get(self.device_id, {}).get(66))

    @property
    def is_opening(self):
        return self._is_moving and self._last_cmd == "open"

    @property
    def is_closing(self):
        return self._is_moving and self._last_cmd == "close"

    async def async_open_cover(self, **kwargs):
        self._last_cmd = "open"
        await self.coordinator.async_set_value(self.device_id, self._pos_id, 0.0)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs):
        self._last_cmd = "close"
        await self.coordinator.async_set_value(self.device_id, self._pos_id, 1.0)
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs):
        target = kwargs.get("position", 0)
        cur = self.current_cover_position
        if cur is not None:
            self._last_cmd = "open" if target > cur else "close"
        pos = 1.0 - (target / 100.0)
        await self.coordinator.async_set_value(self.device_id, self._pos_id, pos)
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs):
        # TapHome nemá dedikovaný stop príkaz — posielame aktuálnu polohu na zastavenie pohybu.
        # TapHome has no dedicated stop command — send current position to halt movement.
        current = self.current_cover_position
        if current is not None:
            await self.coordinator.async_set_value(self.device_id, self._pos_id, 1.0 - (current / 100.0))

    async def async_open_cover_tilt(self, **kwargs):
        await self.coordinator.async_set_value(self.device_id, 10, 0.0)
        await self.coordinator.async_request_refresh()

    async def async_close_cover_tilt(self, **kwargs):
        await self.coordinator.async_set_value(self.device_id, 10, 1.0)
        await self.coordinator.async_request_refresh()

    async def async_set_cover_tilt_position(self, **kwargs):
        tilt = 1.0 - (kwargs.get("tilt_position", 0) / 100.0)
        await self.coordinator.async_set_value(self.device_id, 10, tilt)
        await self.coordinator.async_request_refresh()


# --- TRIEDA 2: BRÁNY (Relé alebo Tlačidlo) ---
class TapHomeDoorCover(TapHomeEntity, CoverEntity):
    def __init__(self, coordinator, device_config, control_id):
        super().__init__(coordinator, device_config)
        self._control_id = control_id
        self._attr_unique_id = f"taphome_gate_{self.device_id}"
        self._attr_device_class = CoverDeviceClass.GARAGE
        self._attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

    @property
    def is_closed(self):
        # Relé (48): stav 0 = zatvorená, 1 = otvorená
        if self._control_id == 48:
            val = self.coordinator.data.get(self.device_id, {}).get(48)
            return val == 0 if val is not None else None
        # Tlačidlo (52): stav neznámy, len impulz
        return None

    async def async_open_cover(self, **kwargs):
        await self.coordinator.async_set_value(self.device_id, self._control_id, 1)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs):
        # Pri tlačidle (52) aj "Zatvoriť" = stlačiť tlačidlo (impulz)
        target_val = 1 if self._control_id == 52 else 0
        await self.coordinator.async_set_value(self.device_id, self._control_id, target_val)
        await self.coordinator.async_request_refresh()
