from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN, CONF_ZONE_COUNT

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
        if user_input is not None:
            self.zone_names = [user_input[f"{CONF_ZONE_COUNT}_{i+1}"] for i in range(self._zone_count)]
            return await self.async_step_switch_selection()

        schema_dict = {}
        for i in range(self._zone_count):
            field_name = f"{CONF_ZONE_COUNT}_{i+1}"
            schema_dict[vol.Required(field_name)] = str

        data_schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id="zone_names",
            data_schema=data_schema
        )

    async def async_step_switch_selection(self, user_input=None):
        if user_input is not None:
            selected_switches = [user_input[f"switch_{i+1}"] for i in range(self._zone_count)]
            return self.async_create_entry(
                title="Setup Completed",
                data={
                    "zone_names": self.zone_names,
                    "selected_switches": selected_switches
                }
            )

        switches = []
        for state in self.hass.states.async_all():
            if state.entity_id.startswith("switch."):
                friendly_name = state.attributes.get("friendly_name", state.entity_id)
                switches.append((state.entity_id, friendly_name))


        switches.sort(key=lambda x: x[1].lower())

        schema_dict = {}
        for i in range(self._zone_count):
            field_name = f"switch_{i+1}"
            schema_dict[vol.Required(field_name)] = vol.In({entity_id: name for entity_id, name in switches})

        data_schema = vol.Schema(schema_dict)

        return self.async_show_form(
            step_id="switch_selection",
            data_schema=data_schema
        )
