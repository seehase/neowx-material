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
    timezone= TODO provide supported values by open-meteo.com

    forecast_charts_order = TODO define supported options
    forecast_values_order = TODO define supported options

"""

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

        # TODO read configuration from skin conf
        # TODO call api with provided configuration to request only needed values
        # TODO process downlaoded hourly data and format it to correct format for charts
        # TODO process downloaded daily data and format it to correct form for value chars
        # TODO return object/collection with all prepared data

        return {
            "foo": "bar"
        }