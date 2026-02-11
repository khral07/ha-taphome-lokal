from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from . import DOMAIN

class TapHomeEntity(CoordinatorEntity):
    # Common ancestor for all TapHome entities. / Spoločný predok pre všetky TapHome entity.

    def __init__(self, coordinator, device_config):
        super().__init__(coordinator)
        self.device_config = device_config
        self.device_id = device_config["deviceId"]
        self._attr_name = device_config["name"]
        self._attr_unique_id = f"taphome_{self.device_id}"

    @property
    def device_info(self):
        # Creates 'Device' in HA and assigns it to an Area. / Vytvorí 'Zariadenie' v HA a priradí ho do Zóny (Miestnosti).
        return DeviceInfo(
            identifiers={(DOMAIN, str(self.device_id))},
            name=self.device_config["name"],
            manufacturer="TapHome",
            model=self.device_config.get("type", "Unknown Device"),
            suggested_area=self.device_config.get("zone"),
            configuration_url="https://taphome.com/",
        )

    @property
    def extra_state_attributes(self):
        # Adds detailed info to entity attributes. / Pridá detailné informácie do atribútov entity.
        return {
            "Taphome ID": self.device_id,
            "Taphome Name": self.device_config.get("name"),
            "Taphome Description": self.device_config.get("description"),
            "Taphome Category": self.device_config.get("category"),
            "Taphome Zone": self.device_config.get("zone"),
            "Taphome Type": self.device_config.get("type"),
        }