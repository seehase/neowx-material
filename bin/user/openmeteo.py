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
    # By enabling forecast you must agree to Terms of use for Non-Commercial Use only. You can read full condition on website https://open-meteo.com/en/terms
    # By non-commercial is considered website without any fees, subscriptions, comertial purpose or advetisement etc. Please read more in Open Meteo terms of use.
    
    # IMPORTANT, if you want to enable forecast
    # 1) To make it work you must add "user.openmeteo.Forecast" in [CheetahGenerator] search_list_extensions section bellow
    # 2) You need to install python requests library using:
    #    in case you installed weewx with pip: "python3 -m pip install requests"
    #    in case you installed weewx with apt: "apt install python3-requests"
    
    # Enable forecast yes / no
    enable_forecast = no 
    # Number of forecast days 1 / 3
    forecast_days = 3
    # Timezone from list of database time zones, or auto will determine timezone from station coordinates
    timezone = auto
    # Type of forecast displayed on page simple / advanced
    type = simple
    # position on page where to show forecast top / middle / bottom
    position = top
"""

import time
import requests
import logging
import math
from collections import Counter

from weewx.cheetahgenerator import SearchList
from weewx.units import ValueHelper, ValueTuple

log = logging.getLogger(__name__)

# global cache variable, we will call api only once in hour
_weather_cache = {
    "timestamp": None,
    "data": None,
}

class Forecast(SearchList):

    def __init__(self, generator):
        SearchList.__init__(self, generator)
        self.latitude = self.generator.stn_info.latitude_f
        self.longitude = self.generator.stn_info.longitude_f
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.forecast_dict = generator.skin_dict.get("Extras", {}).get("Forecast", {})
        self.generator = generator

    def forecast(self):

        enabled = self.forecast_dict.get("enable_forecast", "no")

        if enabled != "yes":
            log.debug("Forecast is disabled")
            return None

        forecast_days = 1
        if int(self.forecast_dict.get("forecast_days", 3)) == 3:
            forecast_days = 3 # just to filter only allowed values 1 / 3

        type = "simple"
        if self.forecast_dict.get("type", "simple") == "advanced":
            type = "advanced" # just to filter only allowed values simple / advanced

        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "forecast_days": forecast_days,
            "timezone": self.forecast_dict.get("timezone", "auto"),
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
            "timeformat": "unixtime",
        }

        hourly = []
        daily = []
        if type == "advanced" or type == "simple":  # common for both
            hourly.append("weather_code")
            daily.append("temperature_2m_min")
            daily.append("temperature_2m_max")
        if type == "advanced":  # additional field for advanced view
            daily.append("uv_index_max")
            daily.append("precipitation_sum")
            daily.append("precipitation_probability_max")
            daily.append("wind_speed_10m_max")
            daily.append("wind_gusts_10m_max")
            daily.append("wind_direction_10m_dominant")

        if len(hourly) > 0:
            params["hourly"] = ",".join(hourly)
        if len(daily) > 0:
            params["daily"] = ",".join(daily)

        log.debug("params: %s", params)

        raw_data = fetch_forecast(self.base_url, params)
        if raw_data is not None:
            return remap_data(self.generator, raw_data, type)

        return None


def fetch_forecast(base_url, params):
    global _weather_cache
    try:
        now = int(time.time())
        current_hour = now - (now % 3600)  # round to full hour
        if _weather_cache["timestamp"] == current_hour:
            log.debug("Using cached data: %s", _weather_cache["data"])
            return _weather_cache["data"]
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        log.debug("Fetched raw data: %s", data)
        # save to cache
        _weather_cache["timestamp"] = current_hour
        _weather_cache["data"] = data
        return data
    except requests.exceptions.HTTPError as e:
        log.error("HTTP error occurred while fetching data:", e)
    except requests.exceptions.RequestException as e:
        log.error("A request error occurred while fetching data:", e)
    except:
        log.error("Unknown exception occured")
    return None


def remap_data(generator, data: dict, type) -> dict:
    # Using ValueHelper will enable easy converting to correct units set by user in weewx.conf
    def build_value_helper(value, unit, group):
        value_tuple = ValueTuple(value, unit, group)
        vh = ValueHelper(
            value_tuple, "current", generator.formatter, generator.converter
        )
        return vh
    
    # Calculate daily weather_code
    daily_weather_codes = []
    hourly_weather_codes = data["hourly"].get("weather_code", [])
    day_count = math.floor(len(hourly_weather_codes) / 24) # calculate number of days of data
    for n in range(day_count):
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
        if type == "advanced" or type == "simple":  # common for both
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
        if type == "advanced":  # additional field for advanced view
            daily_keys["uv_index_max"] = build_value_helper(
                data["daily"].get("uv_index_max", [None])[i],
                "uv_index",
                "group_uv",
            )
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
