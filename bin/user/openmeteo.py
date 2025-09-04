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
    forecast_days=1/3/7
    timezone= auto / or any timezone from list of database time zones

    # For better visualization, variables are not 1:1 representation of open-meteo api but rather groups of related variables
    # temperature =  temperature_2m # will be shown as simple line chart
    # precipitation = precipitation_probability, rain, showers, snowfall # rain + shower + snowfall will be shown as stacked bar chart, precipitation_probability will be asi line chart in same char together
    # cloud_cover = cloud_cover_low, cloud_cover_mid, cloud_cover_high # idealy would be some kind of area chart
    # wind = wind_speed_10m, wind_direction_10m, wind_gusts_10m # maybe area/line chart ?? not sure yet

    forecast_charts_order = temperature, precipitation, cloud_cover, wind

    # Values will show data from daily variables. Card can be wider than usual cards containing some type of table.
    # forecast = weather_code, uv_index_max, temperature_2m_min, temperature_2m_max, precipitation_sum, precipitation_probability_max, wind_speed_10m_max, wind_gusts_10m_max, wind_direction_10m_dominant # shown text forecast based on weather code + weather icon, line per day, with information about min/max temp, UV, precipitation etc.
    # simple_forecast = weather_code # will show only icon representation of weather for today and next day

    forecast_values_order = forecast, simple_forecast

    temperature_unit=celsius/fahrenheit # default is celsius doen't need to be added to api request url
    wind_speed_unit=kmh/ms/mph/kn # default is kmh doen't need to be added to api request url
    precipitation_unit=mm/inch # default is kmh doen't need to be added to api request url
"""

# Time format must be set to timeformat=unixtime fixed, it is required by chart library
# for daily unit it can be converted to daynames based on server timezone

import requests
import logging

from weewx.cheetahgenerator import SearchList

log = logging.getLogger(__name__)


class Forecast(SearchList):

    def __init__(self, generator):
        SearchList.__init__(self, generator)
        self.latitude = self.generator.stn_info.latitude_f
        self.longitude = self.generator.stn_info.longitude_f
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.forecast_dict = generator.skin_dict.get("Forecast", {})
        texts = generator.skin_dict.get("Texts", {})
        self.forecast_texts = texts.get("Forecast", {})

    def forecast(self):

        enabled = self.forecast_dict.get("enable_forecast", "no")

        if enabled != "yes":
            log.debug("Forecast is disabled")
            return {
                "hourly": {
                    "temperature": [],
                    "precipitation": {
                        "probability": [],
                        "rain": [],
                        "showers": [],
                        "snowfall": [],
                    },
                    "cloud_cover": {"low": [], "mid": [], "high": []},
                    "wind": {"speed": [], "direction": [], "gusts": []},
                },
                "daily": {
                    "weather_code": [],
                    "uv_index_max": [],
                    "temperature": {"min": [], "max": []},
                    "precipitation": {
                        "sum": [],
                        "probability": [],
                    },
                    "wind": {"speed": [], "direction": [], "gusts": []},
                },
            }

        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "forecast_days": int(self.forecast_dict.get("forecast_days", 3)),
            "timezone": self.forecast_dict.get("timezone", "auto"),
            "temperature_unit": self.forecast_dict.get("temperature_unit", "celsius"),
            "wind_speed_unit": self.forecast_dict.get("wind_speed_unit", "kmh"),
            "precipitation_unit": self.forecast_dict.get("precipitation_unit", "mm"),
            "timeformat": "unixtime",
        }

        charts = self.forecast_dict.get("forecast_charts_order", [])
        values = self.forecast_dict.get("forecast_values_order", [])

        log.debug("forecast_charts_order:  %s", charts)
        log.debug("forecast_values_order: %s", values)

        hourly = []
        if "temperature" in charts:
            hourly.append("temperature_2m")

        if "precipitation" in charts:
            hourly.append("precipitation_probability")
            hourly.append("rain")
            hourly.append("showers")
            hourly.append("snowfall")

        if "cloud_cover" in charts:
            hourly.append("cloud_cover_low")
            hourly.append("cloud_cover_mid")
            hourly.append("cloud_cover_high")

        if "wind" in charts:
            hourly.append("wind_speed_10m")
            hourly.append("wind_direction_10m")
            hourly.append("wind_gusts_10m")

        if len(hourly) > 0:
            params["hourly"] = ",".join(hourly)

        daily = []
        if "forecast" in values:
            daily.append("weather_code")
            daily.append("uv_index_max")
            daily.append("temperature_2m_min")
            daily.append("temperature_2m_max")
            daily.append("precipitation_sum")
            daily.append("precipitation_probability_max")
            daily.append("wind_speed_10m_max")
            daily.append("wind_gusts_10m_max")
            daily.append("wind_direction_10m_dominant")
        elif "simple_forecast" in values:
            daily.append("weather_code")

        if len(daily) > 0:
            params["daily"] = ",".join(daily)

        log.debug("params: %s", params)

        raw_data = fetchForecast(self.base_url, params)
        return remap_data(raw_data)


def fetchForecast(base_url, params):
    # TODO Use some cache library, cache results for 1 hour to prevent non needed calls, forecast updated once in hour should be plenty enough
    response = requests.get(base_url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    log.debug("Fetched raw data: %s", data)
    return data


def remap_data(data: dict) -> dict:
    def pair_with_time(times, values):
        return [[t, v] for t, v in zip(times, values)]

    # Hourly časové osi
    hourly_time = data.get("hourly", {}).get("time", [])
    daily_time = data.get("daily", {}).get("time", [])

    remapped = {
        "hourly": {
            "temperature": pair_with_time(hourly_time, data["hourly"].get("temperature_2m", [])),
            "precipitation": {
                "probability": pair_with_time(hourly_time, data["hourly"].get("precipitation_probability", [])),
                "rain": pair_with_time(hourly_time, data["hourly"].get("rain", [])),
                "showers": pair_with_time(hourly_time, data["hourly"].get("showers", [])),
                "snowfall": pair_with_time(hourly_time, data["hourly"].get("snowfall", [])),
            },
            "cloud_cover": {
                "low": pair_with_time(hourly_time, data["hourly"].get("cloud_cover_low", [])),
                "mid": pair_with_time(hourly_time, data["hourly"].get("cloud_cover_mid", [])),
                "high": pair_with_time(hourly_time, data["hourly"].get("cloud_cover_high", [])),
            },
            "wind": {
                "speed": pair_with_time(hourly_time, data["hourly"].get("wind_speed_10m", [])),
                "direction": pair_with_time(hourly_time, data["hourly"].get("wind_direction_10m", [])),
                "gusts": pair_with_time(hourly_time, data["hourly"].get("wind_gusts_10m", [])),
            },
        },
        "daily": {
            "weather_code": pair_with_time(daily_time, data["daily"].get("weather_code", [])),
            "uv_index_max": pair_with_time(daily_time, data["daily"].get("uv_index_max", [])),
            "temperature": {
                "min": pair_with_time(daily_time, data["daily"].get("temperature_2m_min", [])),
                "max": pair_with_time(daily_time, data["daily"].get("temperature_2m_max", [])),
            },
            "precipitation": {
                "sum": pair_with_time(daily_time, data["daily"].get("precipitation_sum", [])),
                "probability": pair_with_time(daily_time, data["daily"].get("precipitation_probability_max", [])),
            },
            "wind": {
                "speed": pair_with_time(daily_time, data["daily"].get("wind_speed_10m_max", [])),
                "direction": pair_with_time(daily_time, data["daily"].get("wind_direction_10m_dominant", [])),
                "gusts": pair_with_time(daily_time, data["daily"].get("wind_gusts_10m_max", [])),
            },
        },
    }
    log.debug("Remapped data: %s", remapped)

    return remapped
