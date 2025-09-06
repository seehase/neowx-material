#
# Copyright (c) 2025 Tomáš Filo <tfilosk@gmail.com>
#
# Distributed under the terms of the GNU GENERAL PUBLIC LICENSE
#

"""Extends the Cheetah generator search list to add weather forecast provided by open-meteo.com

[CheetahGenerator]
    search_list_extensions = user.openmeteo.Forecast

[Forecast]
    enable_forecast = yes/no
    forecast_days=1/3
    timezone= auto / or any timezone from list of database time zones

    # Values will show data from daily variables. Use simple or advanced version, not both
    # advanced = weather_code, uv_index_max, temperature_2m_min, temperature_2m_max, precipitation_sum, precipitation_probability_max, wind_speed_10m_max, wind_gusts_10m_max, wind_direction_10m_dominant
    # simple = weather_code, temperature_2m_min, temperature_2m_max # will show only icon representation of weather for today and next day
    type = simple
"""

# Time format must be set to timeformat=unixtime fixed, it is required by chart library
# for daily unit it can be converted to daynames based on server timezone

import time
import requests
import logging

from weewx.cheetahgenerator import SearchList
from weewx.units import ValueHelper, ValueTuple

log = logging.getLogger(__name__)

# global cache variable
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
            type = "advanced" # just to filter only allowed values advanced / simple

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

        daily = []
        if type == "advanced" or type == "simple":  # common for both
            daily.append("weather_code")
            daily.append("temperature_2m_min")
            daily.append("temperature_2m_max")
        if type == "advanced":  # additional field for advanced view
            daily.append("uv_index_max")
            daily.append("precipitation_sum")
            daily.append("precipitation_probability_max")
            daily.append("wind_speed_10m_max")
            daily.append("wind_gusts_10m_max")
            daily.append("wind_direction_10m_dominant")

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

    def build_value_helper(value, unit, group):
        value_tuple = ValueTuple(value, unit, group)
        vh = ValueHelper(
            value_tuple, "current", generator.formatter, generator.converter
        )
        return vh

    # Daily timeline
    daily_time = data.get("daily", {}).get("time", [])

    # Remap daily values
    daily_list = []
    for i, t in enumerate(daily_time):
        dt = build_value_helper(t, "unix_epoch", "group_time")
        daily_keys = {}
        if type == "advanced" or type == "simple":  # common for both
            daily_keys["weather_code"] = data["daily"].get("weather_code", [None])[i]
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
