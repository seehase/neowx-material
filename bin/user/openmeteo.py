#
# Copyright (c) 2025 Tomáš Filo <tfilosk@gmail.com>
#
# Distributed under the terms of the GNU GENERAL PUBLIC LICENSE
#

"""Extends the Cheetah generator search list to add weather forecast provided by open-meteo.com

[CheetahGenerator]
    search_list_extensions = user.openmeteo.Forecast

# Forecast behavior
# -------------------------------------------------------------------------
# Here you can change forecast behavior
#
[[Forecast]]
    # Forecast is provided by website https://open-meteo.com, all data available are under Attribution 4.0 International (CC BY 4.0) (https://creativecommons.org/licenses/by/4.0/)
    # By enabling forecast you must agree to Terms of use for Non-Commercial Use only. You can read full condition on website https://open-meteo.com/en/terms Please read more in Open Meteo terms of use.
    
    # IMPORTANT, READ BEFORE ENABLING FORECAST:
    # 1) To make it work you need to add "user.openmeteo.Forecast" in [CheetahGenerator] search_list_extensions section in this file
    # 2) You need to have installed python requests library, if it is missing in your system you can install using this commands:
    #    in case you installed weewx using pip: "python3 -m pip install requests"
    #    in case you installed weewx using apt: "apt install python3-requests"
    # After installing skin you need to restart weewx service to make it work

    # Errors and troubleshooting:
    # If you see errors like this in your logs, or your skin is not working after enabling forecast:
    # ERROR weewx.cheetahgenerator: Evaluation of template /etc/weewx/skins/neowx-material/index.html.tmpl failed.
    # ERROR weewx.cheetahgenerator: **** Ignoring template /etc/weewx/skins/neowx-material/index.html.tmpl
    # ERROR weewx.cheetahgenerator: **** Reason: cannot find 'forecast'
    # then check [CheetahGenerator] in skin.conf file and make sure you added "user.openmeteo.Forecast" in search_list_extensions section

    # Enable forecast yes / no
    enable = no 
    # Timezone from list of database time zones, or auto will determine timezone from station coordinates
    timezone = auto
    # Type of forecast displayed on page simple / advanced
    type = simple
    # position on page where to show forecast top / middle / bottom
    position = top
"""

import time
import json
import hashlib
import requests
import logging
from collections import Counter

from weewx.cheetahgenerator import SearchList
from weewx.units import ValueHelper, ValueTuple

VERSION = "1.0.0"

log = logging.getLogger(__name__)

# global cache variable, we will call api only once in hour
_weather_cache = {
    "params_hash": None,
    "data": None,
}

class Forecast(SearchList):

    def __init__(self, generator):
        SearchList.__init__(self, generator)
        log.info("version: %s" % VERSION)
        self.latitude = self.generator.stn_info.latitude_f
        self.longitude = self.generator.stn_info.longitude_f
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.forecast_dict = generator.skin_dict.get("Extras", {}).get("Forecast", {})
        self.generator = generator

    def forecast(self):

        enabled = self.forecast_dict.get("enable", "no").lower()
        if enabled != "yes": 
            log.debug("Forecast is disabled")
            return None

        f_type = self.forecast_dict.get("type", "simple").lower()
        if f_type != "advanced" and f_type != "simple": # just to filter only allowed values simple / advanced
            log.info("Parameter type with value '%s' is not valid, simple forecast will be used as fallback.", f_type)
            f_type = "simple" 

        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "forecast_days": 3,
            "timezone": self.forecast_dict.get("timezone", "auto"),
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
            "timeformat": "unixtime",
        }

        hourly = []
        daily = []
        if f_type == "advanced" or f_type == "simple": # common for both
            hourly.append("weather_code")
            daily.append("temperature_2m_min")
            daily.append("temperature_2m_max")
            daily.append("precipitation_sum")
            daily.append("precipitation_probability_max")
        if f_type == "advanced":  # additional field for advanced view
            daily.append("uv_index_max")
            daily.append("wind_speed_10m_max")
            daily.append("wind_gusts_10m_max")
            daily.append("wind_direction_10m_dominant")

        params["hourly"] = ",".join(hourly)
        params["daily"] = ",".join(daily)

        log.debug("params: %s", params)

        return fetch_forecast(self.generator, self.base_url, params, f_type)
    
def hash_params(params, f_type):
    now = int(time.time())
    current_hour = str(now - (now % 3600)) # round to full hour
    params_strigified = json.dumps(params, sort_keys=True) + f_type + current_hour # stringify params and add current hour and type to make sure we will call api only once in hour or if params are changed
    return hashlib.md5(params_strigified.encode()).hexdigest() # create hash from params

def fetch_forecast(generator, base_url, params, f_type):
    global _weather_cache
    try:
        log.debug("Current cache state: %s", _weather_cache)
        params_hash = hash_params(params, f_type)
        if _weather_cache["params_hash"] == params_hash and _weather_cache["data"] is not None:
            log.debug("Using cached data.")
            return _weather_cache["data"]
        else:
            _weather_cache["params_hash"] = None
            _weather_cache["data"] = None
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        log.debug("Fetched raw data: %s", data)
        remaped_data = remap_data(generator, data, f_type)
        # save to cache and return
        _weather_cache["params_hash"] = params_hash
        _weather_cache["data"] = remaped_data
        return _weather_cache["data"]
    except requests.exceptions.HTTPError as e:
        log.info("HTTP error occurred while fetching forecast data from api.open-meteo.com. Enable debug logs in weewx.conf for more details.")
        log.debug(e)
    except requests.exceptions.ConnectionError as e:
        log.info("Connection error occurred while fetching forecast data from api.open-meteo.com. Enable debug logs in weewx.conf for more details.")
        log.debug(e)
    except requests.exceptions.Timeout as e:
        log.info("Fetching forecast data from api.open-meteo.com end up with timeout exception. Enable debug logs in weewx.conf for more details.")
        log.debug(e)
    except requests.exceptions.RequestException as e:
        log.info("A request exception occurred while fetching forecast data from api.open-meteo.com. Enable debug in weewx.conf logs for more details.")
        log.debug(e)
    return None

def remap_data(generator, data: dict, f_type):
    # Using ValueHelper will enable easy converting to correct units set by user in weewx.conf
    def build_value_helper(value, unit, group):
        value_tuple = ValueTuple(value, unit, group)
        vh = ValueHelper(
            value_tuple, "current", generator.formatter, generator.converter
        )
        return vh
    
    try:
        # Calculate daily weather_codes per day by choosing code with highest occurence
        daily_weather_codes = []
        hourly_weather_codes = data.get("hourly", {}).get("weather_code", [])
        if len(hourly_weather_codes) != 72:
            log.info("Forecast data doesn't contain correct number of records for weather code. Skipping forecast and cleaning cached data.")
            _weather_cache["params_hash"] = None
            _weather_cache["data"] = None
            return None
        for n in range(3):
            hourly_weather_codes_for_day = hourly_weather_codes[n*24:(n+1)*24]
            counts = Counter(hourly_weather_codes_for_day)
            max_count = max(counts.values())
            candidates = [val for val, cnt in counts.items() if cnt == max_count]
            result = max(candidates)
            daily_weather_codes.append(result)

        log.debug("Calculated daily weather codes: %s", daily_weather_codes)

        # Daily timeline
        daily_time = data.get("daily", {}).get("time", [])

        # Remap daily values
        daily_list = []
        for i, t in enumerate(daily_time):
            dt = build_value_helper(t, "unix_epoch", "group_time")
            daily_keys = {}
            if f_type == "advanced" or f_type == "simple":  # common for both
                daily_keys["weather_code"] = daily_weather_codes[i]
                daily_keys["temperature"] = {
                    "min": build_value_helper(
                        data["daily"].get("temperature_2m_min", [None])[i],
                        "degree_C",
                        "group_temperature",
                    ),
                    "max": build_value_helper(
                        data["daily"].get("temperature_2m_max", [None])[i],
                        "degree_C",
                        "group_temperature",
                    ),
                }
                daily_keys["precipitation"] = {
                    "sum": build_value_helper(
                        data["daily"].get("precipitation_sum", [None])[i],
                        "mm",
                        "group_rain",
                    ),
                    "probability": build_value_helper(
                        data["daily"].get("precipitation_probability_max", [None])[i],
                        "percent",
                        "group_percent",
                    ),
                }
            if f_type == "advanced":  # additional fields for advanced view
                daily_keys["uv_index_max"] = build_value_helper(
                    data["daily"].get("uv_index_max", [None])[i],
                    "uv_index",
                    "group_uv",
                )
                daily_keys["wind"] = {
                    "speed": build_value_helper(
                        data["daily"].get("wind_speed_10m_max", [None])[i],
                        "km_per_hour",
                        "group_speed",
                    ),
                    "direction": build_value_helper(
                        data["daily"].get("wind_direction_10m_dominant", [None])[i],
                        "degree_compass",
                        "group_direction",
                    ),
                    "gusts": build_value_helper(
                        data["daily"].get("wind_gusts_10m_max", [None])[i],
                        "km_per_hour",
                        "group_speed",
                    ),
                }

            daily_list.append([dt, daily_keys])

        remapped = {
            "daily": daily_list,
        }
        log.debug("Remapped data: %s", remapped)

        return remapped
    except BaseException as e:
        _weather_cache["params_hash"] = None
        _weather_cache["data"] = None
        log.error("Error occured while processing forecast data, cleaning cached data. If this error occure again, please see detailed log below.")
        log.error(e)
    return None