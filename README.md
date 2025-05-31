![Dynamic JSON Badge](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fmarcorm69%2Fzone-smart-irrigation%2Frefs%2Fheads%2Fmain%2Fmanifest.json&query=%24.version&label=version&style=for-the-badge) ![Static Badge](https://img.shields.io/badge/license-Apache%20License%202.0-green?style=for-the-badge&logo=opensourceinitiative&logoColor=%23ffffff) [![Donate with PayPal](https://img.shields.io/badge/donate-paypal-blue?style=for-the-badge&logo=paypal)](https://www.paypal.com/donate/?business=48MF452S8876J&currency_code=EUR)




# Zone Smart Irrigation

Custom integration for Home Assistant to manager a Zone Smart Irrigation System .

> ⚠️ **Nota importante:**  
> This integration is a prerequisite for a smart-irrigation-card 
> https://github.com/marcorm69/smart-irrigation-card


> This guide is still incomplete.  
> The code still has some shortcomings.  
> This work is part of my spare time, I can't give any indication when it will be completed.  

## Disclaimer

This project is distributed in the hope that it will be useful,  
but WITHOUT ANY WARRANTY; without even the implied warranty of  
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  

The author shall not be held liable for any damage or loss caused by the use of this software.  
Use at your own risk.


## License

This project is licensed under the Apache License 2.0.

See the LICENSE file for details.


## Installation

### Manual

1. Copy the files in `custom_components/zone_smart_irrigation` in `config/custom_components/zone-smart-irrigation`
```
<config directory>/
|-- custom_components/
|   |-- zone-smart-irrigation/
|       |-- __init__.py
|       |-- manifest.json
|       |-- config_flow.py
|       |-- number.py
|       |-- etc...
```
2. Restart Home Assistant


## Configuration

For configuration go to UI in **Settings > Integration > Add Integration**, search "Zone Smart Irrigation".

1. Insert number of zones to managed
2. Insert the Zone names
3. Choose the "activator" switch of irrigation (shelly or other for example)

## Using

The integration created the following entity for each zone:
- switch.<zone_name>_on_off
- switch.<zone_name>_slot1_on_off
- switch.<zone_name>_slot2_on_off
- switch.<zone_name>_slot3_on_off
- switch.<zone_name>_slot4_on_off
- switch.<zone_name>_all_week
- switch.<zone_name>_monday
- switch.<zone_name>_tuesday
- switch.<zone_name>_wednesday
- switch.<zone_name>_thursday
- switch.<zone_name>_friday
- switch.<zone_name>_saturday
- switch.<zone_name>_sunday
- number.<zone_name>_slot1_starttime_hour
- number.<zone_name>_slot1_starttime_minute
- number.<zone_name>_slot1_starttime_duration
- number.<zone_name>_slot2_starttime_hour
- number.<zone_name>_slot2_starttime_minute
- number.<zone_name>_slot2_starttime_duration
- number.<zone_name>_slot3_starttime_hour
- number.<zone_name>_slot3_starttime_minute
- number.<zone_name>_slot3_starttime_duration
- number.<zone_name>_slot4_starttime_hour
- number.<zone_name>_slot4_starttime_minute
- number.<zone_name>_slot4_starttime_duration

And this one for all zone:
- sensor.zone_smart_irrigation_config

And this service:
- zone_smart_irrigation.irrigation_control