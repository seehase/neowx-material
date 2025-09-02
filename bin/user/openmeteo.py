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

import weewx
import weewx.units
from datetime import date
import logging

from weewx.cheetahgenerator import SearchList

log = logging.getLogger(__name__)

class Forecast(SearchList):

    def __init__(self, generator):
        SearchList.__init__(self, generator)
        self.latitude = self.generator.stn_info.latitude_f
        self.longitude = self.generator.stn_info.longitude_f
        texts = generator.skin_dict.get('Texts', {})
        self.forecast = texts.get('Forecast', {})

    def forecast(self):

        # TODO analyze possibility and suitability using suggested apis from open-meteo example for python, see: https://open-meteo.com/en/docs?hourly=temperature_2m&timezone=Europe%2FBerlin&forecast_days=3&daily=weather_code,temperature_2m_max,temperature_2m_min,uv_index_max#api_response
        # Do we need all libraries? Cache looks promising, not sure about numpy and pandas, more about api client can be found here https://pypi.org/project/openmeteo-requests/
        # TODO read configuration from skin conf
        # TODO call api with provided configuration to request only needed values
        # TODO process downlaoded hourly data and format it to correct format for charts
        # TODO process downloaded daily data and format it to correct form for value chars
        # TODO return object/collection with all prepared data

        return {
            "foo": "bar"
        }
    

# Expected data format for charts, each chart "line" has own array,
# Look for possibility to emit data in same format as provided in $record variable

# to reuse this code in templates:
# #def getChartData($name, $column)
#   #set current_interval = int($Extras.Charts.current_timespan)
#   #if $name == "rain" or $name == "ET"
#     #set current_interval = int($Extras.Charts.current_rain_timespan)
#   #end if

#   #for $record in $span($day_delta=1).spans(interval=current_interval)
#     #try
#       #set val = $getattr($record, $name)
#       #set data = $getattr($val, $column).format(add_label=False, localize=False, None_string="null")
#       [$record.start.raw, $data],
#     #except

#     #end try
#   #end for
# #end def

# {
#     name: "Temperature"
#     data: [
#         [1756755300, 19.8],
#         [1756755900, 19.5],
#         [1756756500, 19.4],
#         [1756757100, 19.1]
#     ]
# }
