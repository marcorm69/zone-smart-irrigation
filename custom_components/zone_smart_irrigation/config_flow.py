#
#  config_flow.py
#
from homeassistant import config_entries
import voluptuous as vol
from homeassistant.helpers import selector
from .const import DOMAIN, CONF_ZONE_COUNT
import logging

_LOGGER = logging.getLogger(__name__)

class ZoneSmartIrrigationFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self._zone_count = user_input[CONF_ZONE_COUNT]
            return await self.async_step_zone_names()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_ZONE_COUNT, default=1): vol.All(vol.Coerce(int), vol.Range(min=1, max=11))
            })
        )

    async def async_step_zone_names(self, user_input=None):
        errors = {}
        
        if user_input is not None:
            # Definiamo zone_names dall'input
            zone_names = [user_input[f"zone_name_{i+1}"] for i in range(self._zone_count)]
            
            # CONTROLLO DUPLICATI NEL FORM CORRENTE
            if len(zone_names) != len(set(zone_names)):
                errors["base"] = "Nomi zona duplicati. Ogni zona deve avere un nome unico."
            else:
                # CONTROLLO DUPLICATI CON ALTRE CONFIG ENTRIES
                existing_zones = set()
                for entry in self.hass.config_entries.async_entries(DOMAIN):
                    # Recupera i nomi delle zone esistenti
                    if "zone_names" in entry.data:
                        entry_zones = entry.data.get("zone_names", [])
                        existing_zones.update(zone.lower().strip() for zone in entry_zones)
                
                # Controlla conflitti (case-insensitive)
                input_zones_lower = [zone.lower().strip() for zone in zone_names]
                conflicts = existing_zones.intersection(input_zones_lower)
                
                if conflicts:
                    errors["base"] = f"Zone già esistenti: {', '.join(conflicts)}"
                else:
                    # Solo se non ci sono errori, salviamo in self.zone_names
                    self.zone_names = zone_names
                    return await self.async_step_switch_selection()

        # Se ci sono errori o è la prima volta, mostra il form
        schema_dict = {}
        for i in range(self._zone_count):
            field_name = f"zone_name_{i+1}"
            schema_dict[vol.Required(field_name)] = str

        data_schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id="zone_names",
            data_schema=data_schema,
            errors=errors
        )

    async def async_step_switch_selection(self, user_input=None):
        if user_input is not None:
            selected_switches = [user_input[f"switch_{i+1}"] for i in range(self._zone_count)]

            # Crea un titolo significativo concatenando i nomi delle zone
            if len(self.zone_names) == 1:
                title = f"Irrigazione: {self.zone_names[0]}"
            elif len(self.zone_names) <= 3:
                title = f"Irrigazione: {', '.join(self.zone_names)}"
            else:
                # Se ci sono molte zone, mostra solo le prime 2 + "..."
                title = f"Irrigazione: {', '.join(self.zone_names[:2])}... (+{len(self.zone_names)-2})"

            # Crea una singola entry con tutti i dati
            entry_data = {
                "zone_count": self._zone_count,
                "zone_names": self.zone_names,
                "selected_switches": selected_switches
            }
            
            return self.async_create_entry(
                title=title,
                data=entry_data
            )

        # Ottieni tutti gli switch disponibili
        switches = []
        for state in self.hass.states.async_all():
            if state.entity_id.startswith("switch."):
                friendly_name = state.attributes.get("friendly_name", state.entity_id)
                switches.append((state.entity_id, friendly_name))

        switches.sort(key=lambda x: x[1].lower())

        # Crea lo schema per la selezione degli switch
        schema_dict = {}
        for i in range(self._zone_count):
            field_name = f"switch_{i+1}"
            schema_dict[vol.Required(field_name)] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(value=entity_id, label=f"{name} ({entity_id})")
                        for entity_id, name in switches
                    ]
                )
            )

        data_schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id="switch_selection",
            data_schema=data_schema,
            description_placeholders={
                "zone_list": ", ".join(f"{i+1}. {name}" for i, name in enumerate(self.zone_names))
            }
        )