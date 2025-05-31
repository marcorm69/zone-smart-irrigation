from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ZoneConfigSensor(entry.entry_id, data)])

class ZoneConfigSensor(SensorEntity):
    def __init__(self, entry_id, data):
        self._entry_id = entry_id
        self._zone_names = data["zone_names"]
        self._switches = data["switches"]
        self._attr_name = "Zone Smart Irrigation Config"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_config"
        self._attr_state = "configured"

    @property
    def state(self):
        return self._attr_state

    @property
    def extra_state_attributes(self):
        return {
            "zones": self._zone_names,
            "switches": self._switches,
        }
