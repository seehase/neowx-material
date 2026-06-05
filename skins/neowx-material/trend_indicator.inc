#encoding UTF-8
## ---------------------------------------------------------------------------
## Trend indicator for observation $name (the "current" page).
## The caller has already confirmed $name is in Extras.Appearance.show_trend_on
## and that trend.<name>.raw is not None.
##
## The up / steady / down decision is made on a UNIT-INDEPENDENT value: the
## trend is converted to a canonical unit per observation, so the arrows
## behave the same in metric and imperial (e.g. a barometer delta is always
## judged in hPa, never 0.5 inHg ~= 17 hPa).
##
## Barometric pressure additionally follows the WMO/NWS 3-hour pressure
## tendency categories, scaled to the configured trend window, shown with MDI
## single / double / triple chevrons:
##   < 0.1 hPa/3h  steady          (wi-direction-right)
##   < 3.6         rising/falling  (mdi-chevron-up/down)
##   < 6.0         quickly         (mdi-chevron-double-up/down)
##   >= 6.0        very rapidly    (mdi-chevron-triple-up/down)
## Every other observation uses the simple up / steady / down arrow with a
## per-observation dead-band.
## ---------------------------------------------------------------------------
#set $_pressure = $name in ('barometer', 'pressure', 'altimeter')
## Per-observation [canonical unit ('' = use the display unit), dead-band].
#set $_bands = {'outTemp': ['degree_C', 0.5], 'inTemp': ['degree_C', 0.5], 'ET': ['mm', 0.02]}
#set $_cfg  = $_bands.get($name, ['', 0.5])
#set $_unit = 'mbar' if $_pressure else $_cfg[0]
#set $_band = $_cfg[1]
## Trend delta in the canonical unit (fall back to the display unit on error).
#set $_vh = $getVar('trend.' + $name)
#try
    #if $_unit
        #set $_tv = $getattr($_vh, $_unit).raw
    #else
        #set $_tv = $_vh.raw
    #end if
#except
    #set $_tv = $_vh.raw
#end try
#set $_when = $trend.time_delta.hour
#if $_tv is not None
    #if $_pressure
        ## Scale the 3-hour standard to the actual trend window.
        #try
            #set $_scale = float($getVar('trend.time_delta.hour.raw')) / 3.0
        #except
            #set $_scale = 1.0
        #end try
        #if $_scale <= 0
            #set $_scale = 1.0
        #end if
        #set $_mag = abs($_tv)
        #if $_mag < 0.1 * $_scale
            <i class="wi wi-direction-right" title="$gettext('trend'): $_vh ($_when)" data-toggle="tooltip" data-html="true"></i>
        #else
            #set $_dir = 'up' if $_tv > 0 else 'down'
            #if $_mag >= 6.0 * $_scale
                #set $_chev = 'mdi-chevron-triple-' + $_dir
                #set $_word = 'Rising very rapidly' if $_dir == 'up' else 'Falling very rapidly'
            #else if $_mag >= 3.6 * $_scale
                #set $_chev = 'mdi-chevron-double-' + $_dir
                #set $_word = 'Rising quickly' if $_dir == 'up' else 'Falling quickly'
            #else
                #set $_chev = 'mdi-chevron-' + $_dir
                #set $_word = 'Rising' if $_dir == 'up' else 'Falling'
            #end if
            <i class="mdi $_chev" title="$_word: $_vh ($_when)" data-toggle="tooltip" data-html="true"></i>
        #end if
    #else
        #if $_tv > $_band
            <i class="wi wi-direction-up-right" title="$gettext('trend'): $_vh ($_when)" data-toggle="tooltip" data-html="true"></i>
        #else if $_tv < -$_band
            <i class="wi wi-direction-down-right" title="$gettext('trend'): $_vh ($_when)" data-toggle="tooltip" data-html="true"></i>
        #else
            <i class="wi wi-direction-right" title="$gettext('trend'): $_vh ($_when)" data-toggle="tooltip" data-html="true"></i>
        #end if
    #end if
#end if
