from homeassistant.components.number import NumberEntity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import Entity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    zone_names = data["zone_names"]

    entities = []

    for zone in zone_names:
        # Manual duration per zona (es. orto_manual_duration)
        entities.append(ZoneManualDurationNumber(entry.entry_id, zone))

        # Slot 1..4: starttime_hour, starttime_minute, duration
        for slot in range(1, 5):
            entities.append(ZoneSlotStartHourNumber(entry.entry_id, zone, slot))
            entities.append(ZoneSlotStartMinuteNumber(entry.entry_id, zone, slot))
            entities.append(ZoneSlotDurationNumber(entry.entry_id, zone, slot))

    async_add_entities(entities)

# Base class con persistenza su hass.data (puoi migliorare salvando su file, storage ecc)
#class BaseZoneNumber(NumberEntity):
class BaseZoneNumber(RestoreEntity, NumberEntity):

    def __init__(self, entry_id, zone, name):
        self._entry_id = entry_id
        self._zone = zone
        self._attr_name = f"{zone.upper()} {name}"
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{zone}_{name.replace(' ', '_').lower()}"
        self._attr_native_value = 0  # Usa native_value per NumberEntity

    @property
    def native_value(self):  # Cambia da 'value' a 'native_value'
        return self._attr_native_value

    async def async_set_native_value(self, value: float) -> None:  # Cambia nome metodo
        self._attr_native_value = int(value)
        self.async_write_ha_state()
        
    async def async_added_to_hass(self):
        """Restore previous state."""
        await super().async_added_to_hass()
        old_state = await self.async_get_last_state()
        if old_state is not None and old_state.state not in (None, "unknown", "unavailable"):
            try:
                self._attr_native_value = float(old_state.state)
            except (ValueError, TypeError):
                self._attr_native_value = 0


# Manual duration per zona
class ZoneManualDurationNumber(BaseZoneNumber):
    def __init__(self, entry_id, zone):
        super().__init__(entry_id, zone, "manual duration")
        self._attr_min_value = 1
        self._attr_max_value = 3600  # max 1 ora (in secondi o minuti, scegli tu)
        self._attr_step = 1

# Slot starttime hour
class ZoneSlotStartHourNumber(BaseZoneNumber):
    def __init__(self, entry_id, zone, slot):
        super().__init__(entry_id, zone, f"slot{slot} starttime hour")
        self._attr_min_value = 0
        self._attr_max_value = 23
        self._attr_step = 1

# Slot starttime minute
class ZoneSlotStartMinuteNumber(BaseZoneNumber):
    def __init__(self, entry_id, zone, slot):
        super().__init__(entry_id, zone, f"slot{slot} starttime minute")
        self._attr_min_value = 0
        self._attr_max_value = 59
        self._attr_step = 1

# Slot duration
class ZoneSlotDurationNumber(BaseZoneNumber):
    def __init__(self, entry_id, zone, slot):
        super().__init__(entry_id, zone, f"slot{slot} duration")
        self._attr_min_value = 1
        self._attr_max_value = 3600  # max 1 ora (o come vuoi)
        self._attr_step = 1
