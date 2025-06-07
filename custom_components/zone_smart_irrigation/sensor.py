#
#  sensor.py
#
from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    # Controlla se il sensore globale esiste già
    existing_sensor = None
    for entity_id in hass.states.async_entity_ids("sensor"):
        if entity_id == "sensor.zone_smart_irrigation_config":
            # Il sensore esiste già, non crearne un altro
            existing_sensor = hass.data.get(f"{DOMAIN}_global_sensor")
            break
    
    if existing_sensor is None:
        # Crea il sensore globale solo se non esiste
        global_sensor = ZoneConfigSensor(hass)
        hass.data[f"{DOMAIN}_global_sensor"] = global_sensor
        async_add_entities([global_sensor])
    else:
        # Il sensore esiste già, aggiorna i suoi dati
        existing_sensor.update_zones_from_entries()

class ZoneConfigSensor(SensorEntity):
    def __init__(self, hass):
        self._hass = hass
        self._attr_name = "Zone Smart Irrigation Config"
        self._attr_unique_id = f"{DOMAIN}_config"  # Unico ID globale
        self._attr_state = "configured"
        self._zone_names = []
        self._switches = []
        # NON chiamare update_zones_from_entries() qui!
    
    async def async_added_to_hass(self):
        """Chiamato quando l'entità viene aggiunta a Home Assistant."""
        await super().async_added_to_hass()
        # Ora è sicuro aggiornare i dati e lo stato
        self.update_zones_from_entries()
    
    def update_zones_from_entries(self, exclude_entry_id=None):
        """Aggiorna le zone leggendo da tutte le config entries."""
        all_zones = []
        all_switches = []
        
        # Raccogli zone da tutte le config entries del tuo DOMAIN, ESCLUDENDO quella specificata
        for entry in self._hass.config_entries.async_entries(DOMAIN):
            # Salta l'entry che stiamo escludendo (quella che viene rimossa)
            if exclude_entry_id and entry.entry_id == exclude_entry_id:
                continue
                
            entry_zones = entry.data.get("zone_names", [])
            entry_switches = entry.data.get("selected_switches", [])
            
            all_zones.extend(entry_zones)
            all_switches.extend(entry_switches)
        
        self._zone_names = all_zones
        self._switches = all_switches
        
        # Aggiorna lo stato solo se l'entità è già registrata
        if hasattr(self, 'hass') and self.hass is not None and hasattr(self, 'registry_entry'):
            self.async_write_ha_state()

    @property
    def state(self):
        return self._attr_state

    @property
    def extra_state_attributes(self):
        return {
            "zones": self._zone_names,
            "switches": self._switches,
        }