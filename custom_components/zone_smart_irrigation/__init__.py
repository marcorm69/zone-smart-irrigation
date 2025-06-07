# 
#	__init.py
#
import asyncio
import logging
from datetime import datetime, time
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import entity_registry as er
from homeassistant.components.automation import DOMAIN as AUTOMATION_DOMAIN
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_time_change
from homeassistant.core import callback
from datetime import datetime
from homeassistant.config_entries import ConfigEntryState

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
def _slugify(name: str) -> str:
    """Convert zone name to slug format."""
    return name.lower().replace(' ', '_').replace('-', '_')

async def async_setup_entry(hass, entry):
    zone_names = entry.data["zone_names"]
    selected_switches = entry.data["selected_switches"]

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "zone_names": zone_names,
        "switches": selected_switches,
        "active_irrigations": {}  # Traccia irrigazioni attive
    }

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "number", "switch"])

    # === SERVIZIO UNIFICATO ===
    async def irrigation_service(call: ServiceCall):
        """Servizio unificato per irrigazione: start/stop con timer automatico."""
        
        action = call.data.get("action", "start")  # start/stop
        switch_entity = call.data.get("switch_entity")
        duration_minutes = call.data.get("duration", 0)
        
        _LOGGER.info(f"Servizio irrigazione: {action} - switch: {switch_entity} - durata: {duration_minutes}min")
        
        try:
            if action == "start":
                await _start_irrigation(hass, switch_entity, duration_minutes)
            elif action == "stop":
                await _stop_irrigation(hass, switch_entity)
            else:
                _LOGGER.error(f"Azione non riconosciuta: {action}")
                
        except Exception as e:
            _LOGGER.error(f"Errore nel servizio irrigazione: {e}")

    async def _start_irrigation(hass, switch_entity, duration_minutes):
        """Avvia irrigazione con timer automatico."""
        
        # Verifica se già attiva
        active_irrigations = hass.data[DOMAIN][entry.entry_id]["active_irrigations"]
        if switch_entity in active_irrigations:
            _LOGGER.warning(f"Irrigazione già attiva per {switch_entity}")
            return
        
        # Accendi lo switch
        await hass.services.async_call("switch", "turn_on", {"entity_id": switch_entity})
        _LOGGER.info(f"Switch {switch_entity} acceso per {duration_minutes} minuti")
        
        # Crea task per spegnimento automatico
        async def auto_stop():
            await asyncio.sleep(duration_minutes * 60)
            await _stop_irrigation(hass, switch_entity)
            _LOGGER.info(f"Irrigazione terminata automaticamente: {switch_entity}")
        
        # Salva il task per poterlo cancellare se necessario
        task = hass.async_create_task(auto_stop())
        active_irrigations[switch_entity] = task

    async def _stop_irrigation(hass, switch_entity):
        """Ferma irrigazione e cancella timer."""
        
        active_irrigations = hass.data[DOMAIN][entry.entry_id]["active_irrigations"]
        
        # Cancella timer se esiste
        if switch_entity in active_irrigations:
            active_irrigations[switch_entity].cancel()
            del active_irrigations[switch_entity]
        
        # Spegni lo switch
        await hass.services.async_call("switch", "turn_off", {"entity_id": switch_entity})
        _LOGGER.info(f"Irrigazione fermata: {switch_entity}")

    # Registra il servizio
    hass.services.async_register(
        DOMAIN,
        "irrigation_control",
        irrigation_service,
        schema=vol.Schema({
            vol.Optional("action", default="start"): cv.string,
            vol.Required("switch_entity"): cv.string,
            vol.Optional("duration", default=10): vol.All(vol.Coerce(float), vol.Range(min=1, max=240))
        })
    )

    # === CREA AUTOMAZIONI DINAMICHE ===
    await _create_irrigation_automations(hass, zone_names, selected_switches, entry.entry_id)
    
    return True

async def _create_irrigation_automations(hass, zone_names, selected_switches, entry_id):
    """Setup automatic scheduling for all zones."""
    
    # Inizializza la lista dei listeners per il cleanup
    hass.data[DOMAIN][entry_id]["listeners"] = []
    
    # Setup automazione per ogni zona
    for zone_name in zone_names:
        await _setup_zone_automation(hass, zone_name, entry_id)
    
    _LOGGER.info(f"✅ Sistema irrigazione programmata attivato per {len(zone_names)} zone(e)")


async def _setup_zone_automation(hass, zone_name: str, entry_id: str):
    """Set up automatic scheduling for a zone."""
    
    # Recupera i dati dell'integrazione
    instance_data = hass.data[DOMAIN].get(entry_id)
    if not instance_data:
        _LOGGER.error(f"Instance data for entry_id {entry_id} not found.")
        return

    listeners = instance_data.setdefault("listeners", [])
    zone_names = instance_data["zone_names"]
    selected_switches = instance_data["switches"]
    
    # Trova lo switch associato a questa zona
    try:
        zone_index = zone_names.index(zone_name)
        switch_entity = selected_switches[zone_index]
    except (ValueError, IndexError):
        _LOGGER.error(f"Switch not found for zone {zone_name}")
        return
    
    zone_slug = _slugify(zone_name)
    
    @callback
    async def check_slot_time(now: datetime):
        """Controlla se è ora di avviare l'irrigazione per questa zona."""
        
        # Recupera i dati aggiornati
        instance_data = hass.data[DOMAIN].get(entry_id)
        if not instance_data:
            _LOGGER.error(f"Instance data for entry_id {entry_id} not found in check_slot_time.")
            return

        _LOGGER.debug(f"Checking slots for {zone_name} at {now}.")
        
        # Controlla tutti i 4 slot
        for slot in range(1, 5):
            slot_switch = f"switch.{zone_slug}_slot{slot}_on_off"
            zone_main_switch = f"switch.{zone_slug}_on_off"
            
            _LOGGER.debug(f"Checking slot {slot} - Switch: {slot_switch}.")
            
            # Verifica che lo switch principale della zona sia ON
            if not hass.states.is_state(zone_main_switch, "on"):
                _LOGGER.debug(f"Zone {zone_name} main switch disabled.")
                continue
            
            # Verifica che lo switch dello slot sia ON
            if not hass.states.is_state(slot_switch, "on"):
                _LOGGER.debug(f"Slot {slot} disabled.")
                continue
            
            # Controlla i giorni della settimana
            today = now.strftime("%A").lower()
            allweek = hass.states.is_state(f"switch.{zone_slug}_allweek", "on")
            today_enabled = hass.states.is_state(f"switch.{zone_slug}_{today}", "on")
            
            _LOGGER.debug(f"Day check - All week: {allweek}, Today ({today}): {today_enabled}.")
            
            if not allweek and not today_enabled:
                _LOGGER.debug("Day not enabled.")
                continue
            
            # Controlla l'orario
            hour_entity = f"number.{zone_slug}_slot{slot}_starttime_hour"
            minute_entity = f"number.{zone_slug}_slot{slot}_starttime_minute"
            
            try:
                hour_state = hass.states.get(hour_entity)
                minute_state = hass.states.get(minute_entity)

                if not hour_state or not minute_state:
                    _LOGGER.warning(f"Time entities for slot {slot} ({hour_entity}, {minute_entity}) not found.")
                    continue

                target_hour = int(float(hour_state.state))
                target_minute = int(float(minute_state.state))
                _LOGGER.debug(f"Slot {slot} target time: {target_hour:02d}:{target_minute:02d}.")
                
                # È l'orario giusto?
                if now.hour == target_hour and now.minute == target_minute:
                    duration_entity = f"number.{zone_slug}_slot{slot}_duration"
                    duration_state = hass.states.get(duration_entity)
                    
                    if not duration_state:
                        _LOGGER.warning(f"Duration entity {duration_entity} not found.")
                        continue
                    
                    duration = float(duration_state.state)
                    
                    _LOGGER.info(f"🌱 Triggering irrigation for {zone_name} slot {slot} - {duration} minutes.")
                    
                    # Chiama il servizio di irrigazione
                    await hass.services.async_call(
                        DOMAIN,
                        "irrigation_control",
                        {
                            "action": "start",
                            "switch_entity": switch_entity,
                            "duration": duration
                        }
                    )
                    
            except (AttributeError, ValueError) as err:
                _LOGGER.error(f"Error checking slot {slot} for zone '{zone_name}': {err}.")

    # Registra il listener per questa zona
    cancel_listener = async_track_time_change(hass, check_slot_time, second=0)
    listeners.append(cancel_listener)
    
    _LOGGER.info(f"📅 Scheduling attivo per zona: {zone_name}")

async def async_unload_entry(hass, entry):
    """Cleanup quando l'integrazione viene rimossa."""
    
    entry_data = hass.data[DOMAIN].get(entry.entry_id, {})
    
    # Ferma tutte le irrigazioni attive per questa entry
    active_irrigations = entry_data.get("active_irrigations", {})
    for switch_entity, task in active_irrigations.items():
        task.cancel()
        _LOGGER.info(f"Irrigazione interrotta: {switch_entity}")
    
    # Cancella tutti i listeners per la programmazione di questa entry
    listeners = entry_data.get("listeners", [])
    for cancel_listener in listeners:
        cancel_listener()
    
    if listeners:
        _LOGGER.info(f"Sistema irrigazione programmata disattivato ({len(listeners)} zone)")
    
    # Rimuovi i dati di questa entry
    hass.data[DOMAIN].pop(entry.entry_id, None)
    
    # Controlla se ci sono ancora altre entry attive
    remaining_entries = [
        e for e in hass.config_entries.async_entries(DOMAIN) 
        if e.entry_id != entry.entry_id and e.state.name == "LOADED"
    ]
    
    # Aggiorna il sensore globale con i dati delle entry rimanenti
    global_sensor = hass.data.get(f"{DOMAIN}_global_sensor")
    if global_sensor and hasattr(global_sensor, 'hass') and global_sensor.hass is not None:
        try:
            if remaining_entries:
                # Ci sono ancora entry attive, aggiorna il sensore ESCLUDENDO l'entry che stiamo rimuovendo
                global_sensor.update_zones_from_entries(exclude_entry_id=entry.entry_id)
                _LOGGER.info(f"Sensore globale aggiornato, rimangono {len(remaining_entries)} entry")
            else:
                # Non ci sono più entry, ADESSO sì che rimuovi il sensore
                await global_sensor.async_remove()
                hass.data.pop(f"{DOMAIN}_global_sensor", None)
                _LOGGER.info("Sensore globale rimosso - nessuna entry rimanente")
        except Exception as e:
            _LOGGER.warning(f"Errore aggiornando sensore globale durante unload: {e}")
    
    # RIMUOVI SERVIZI E COMPONENTI CONDIVISI SOLO SE NON CI SONO PIÙ ENTRY
    if not remaining_entries:
        # Non ci sono più entry, rimuovi i servizi condivisi
        if hass.services.has_service(DOMAIN, "irrigation_control"):
            hass.services.async_remove(DOMAIN, "irrigation_control")
            _LOGGER.info("Servizio irrigation_control rimosso")
        
        # Cleanup completo dei dati del dominio
        if DOMAIN in hass.data:
            hass.data.pop(DOMAIN)
            _LOGGER.info("Dati del dominio puliti completamente")
    else:
        _LOGGER.info(f"Servizi mantenuti - rimangono {len(remaining_entries)} entry attive")

    # Unload platforms per questa entry specifica
    await hass.config_entries.async_unload_platforms(entry, ["sensor", "number", "switch"])
    
    return True