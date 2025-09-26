#encoding UTF-8
## +-------------------------------------------------------------+
## |    forecast.inc                       Forecast templates    |
## +-------------------------------------------------------------+

#set $weatherMap = {
    0: "wi-day-sunny",
    1: "wi-day-sunny-overcast",
    2: "wi-day-cloudy",
    3: "wi-cloudy",
    45: "wi-day-fog",
    48: "wi-day-fog",
    51: "wi-day-sprinkle",
    53: "wi-day-sprinkle",
    55: "wi-day-sprinkle",
    56: "wi-day-sprinkle",
    57: "wi-day-sprinkle",
    61: "wi-day-showers",
    63: "wi-day-showers",
    65: "wi-day-rain",
    66: "wi-day-showers",
    67: "wi-day-rain",
    71: "wi-day-snow",
    73: "wi-day-snow",
    75: "wi-day-snow",
    77: "wi-day-snow",
    80: "wi-day-showers",
    81: "wi-day-rain",
    82: "wi-day-rain",
    85: "wi-day-snow",
    86: "wi-day-snow",
    95: "wi-day-storm-showers",
    96: "wi-day-thunderstorm",
    99: "wi-day-thunderstorm"
}

#if $Extras.Forecast.get("enable", "no").lower() == "yes" and $forecast is not None
  <div class="col-12 mb-4">
    <div class="card">
      <div class="card-body text-center pb-1">
        <h3 class="h5-responsive $Extras.color-text">
            $pgettext("Forecast","daily")
        </h3>
        #if $Extras.Forecast.get("type", "simple").lower() == "simple"
          <div class="d-flex">
          #for $x in $forecast.daily
            <div class="flex-fill">
              <div class="text-nowrap $Extras.color-text">
                $x[0].format("%A")
              </div>
              <i class="display-3 py-4 wi $weatherMap.get($x[1].weather_code, "wi-na")" title="$pgettext("Forecast",str($x[1].weather_code))" data-toggle="tooltip" data-html="true"></i>
              <div class="font-small" title="$pgettext("Forecast","min_temp") / $pgettext("Forecast","max_temp")">
                $x[1].temperature.min / $x[1].temperature.max
              </div>
              <div class="font-small" title="$pgettext("Forecast","precipitation") ($pgettext("Forecast","probability"))">
                $x[1].precipitation.sum ($x[1].precipitation.probability)
              </div>
            </div>
          #end for
          </div>
        #end if
        #if $Extras.Forecast.get("type", "simple").lower() == "advanced"
          <div class="d-lg-flex">
          #set $count = 0
          #set $total = len($forecast.daily)
          #for $x in $forecast.daily
            <div class="row flex-fill font-small">
              <div class="col-4 text-nowrap $Extras.color-text">
                $x[0].format("%A")
              </div>
              <div class="col-8 text-left">
                $pgettext("Forecast",str($x[1].weather_code))
              </div>
              <div class="col-4 $Extras.color-text">
                <i class="wi wi-thermometer" title="$pgettext("Forecast","min_temp") / $pgettext("Forecast","max_temp")" data-toggle="tooltip" data-html="true"></i>
              </div>
              <div class="col-8 text-left">
                $x[1].temperature.min / $x[1].temperature.max
              </div>
              <div class="col-4 $Extras.color-text">
                <i class="wi wi-day-sunny" title="$pgettext("Forecast","uv")" data-toggle="tooltip" data-html="true"></i>
              </div>
              <div class="col-8 text-left">
                $x[1].uv_index_max
              </div>
              <div class="col-4 $Extras.color-text">
                <i class="wi wi-umbrella" title="$pgettext("Forecast","precipitation") ($pgettext("Forecast","probability"))" data-toggle="tooltip" data-html="true"></i>
              </div>
              <div class="col-8 text-left">
                $x[1].precipitation.sum ($x[1].precipitation.probability)
              </div>
              <div class="col-4 $Extras.color-text">
                <i class="wi wi-strong-wind" title="$pgettext("Forecast","wind_speed") & $pgettext("Forecast","wind_dir") ($pgettext("Forecast","wind_gust"))" data-toggle="tooltip" data-html="true"></i>
              </div>
              <div class="col-8 text-left">
                $x[1].wind.speed <i class="wi wi-wind from-$x[1].wind.direction.formatted-deg mr-2" title="$x[1].wind.direction.formatted°" data-toggle="tooltip" data-html="true"></i> ($x[1].wind.gusts)
              </div>
            </div>
            #set $count = $count + 1
            #if $count != $total
              <hr class="rowdivider"/>
            #end if
          #end for
          </div>
        #end if
        <div class="text-muted font-extra-small text-right">
        	Forecast by&nbsp;<a class="text-muted" href="https://open-meteo.com/">Open-Meteo.com</a>
    	  </div>
      </div>
    </div>
  </div>
#end if
