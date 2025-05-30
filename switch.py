from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    zone_names = data["zone_names"]
    entities = []

    for zone in zone_names:
        zone_id = zone.lower()
        zone_label = zone.upper()

        # On/Off switch
        entities.append(ZoneSwitch(f"{zone_id}_onoff", f"{zone_label} On/Off"))

        # All week
        entities.append(ZoneSwitch(f"{zone_id}_allweek", f"{zone_label} All Week"))

        # Days of week
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
            entities.append(ZoneSwitch(f"{zone_id}_{day}", f"{zone_label} {day.title()}"))

        # Slot switches
        for i in range(1, 5):
            entities.append(ZoneSwitch(f"{zone_id}_slot{i}_onoff", f"{zone_label} Slot{i} On/Off"))

    async_add_entities(entities)


class ZoneSwitch(RestoreEntity, SwitchEntity):

    def __init__(self, switch_id, name):
        self._attr_name = name
        self._attr_unique_id = f"zone_smart_irrigation_{switch_id}"
        self._is_on = False

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._is_on = False
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Restore previous state."""
        await super().async_added_to_hass()
        old_state = await self.async_get_last_state()
        if old_state is not None:
            self._is_on = old_state.state == "on"

