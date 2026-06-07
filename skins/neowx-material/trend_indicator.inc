#encoding UTF-8
## ---------------------------------------------------------------------------
## Trend indicator for observation $name (the "current" page).
## A Cheetah #include has its own scope and cannot see the caller's local
## $name, so the caller passes it via the $_trend_obs global. The caller only
## guarantees $name is in show_trend_on.
##
## We compute the change OURSELVES rather than use WeeWX $trend (which returns
## None unless an archive record lands within a small grace window of exactly
## now - time_delta): (current reading) - (oldest reading in the last N hours,
## via span(hour_delta=N).<obs>.first). That has a value whenever there is any
## recent data.
##
## The direction is decided in a CANONICAL unit per unit-family, derived from
## the obs's current display unit, so trends behave identically in metric and
## imperial for ANY observation. Units not listed (percent, UV index, ppm,
## ug/m3, W/m2, counts) are already comparable across systems -> no conversion.
##
## Barometric pressure additionally uses the WMO/NWS 3-hour tendency categories
## (steady / slowly / quickly / very rapidly) shown with Weather-Icons arrows
## (steeper = faster; two arrows = very rapidly). Everything else uses a simple
## up / steady / down arrow with a per-family dead-band. The tooltip shows the
## change in the user's display units.
## ---------------------------------------------------------------------------
#set $name = $_trend_obs
#set $_hours = 3
#set $_pressure = $name in ('barometer', 'pressure', 'altimeter')
## display unit -> canonical unit (only families whose unit varies by system)
#set $_canon = {
    'inHg':'mbar', 'mmHg':'mbar', 'kPa':'mbar', 'hPa':'mbar', 'mbar':'mbar',
    'degree_F':'degree_C', 'degree_K':'degree_C', 'degree_C':'degree_C',
    'inch':'mm', 'cm':'mm', 'mm':'mm',
    'inch_per_hour':'mm_per_hour', 'cm_per_hour':'mm_per_hour', 'mm_per_hour':'mm_per_hour',
    'mile_per_hour':'km_per_hour', 'knot':'km_per_hour', 'meter_per_second':'km_per_hour', 'beaufort':'km_per_hour', 'km_per_hour':'km_per_hour',
    'foot':'meter', 'meter':'meter', 'mile':'km', 'km':'km'
}
## "steady" dead-band per canonical unit (default 0.5 for unit-agnostic obs)
#set $_deadbands = {'degree_C':0.5, 'mm':0.2, 'mm_per_hour':0.2, 'km_per_hour':1.0, 'meter':10.0, 'km':0.5}
#set $_unit = $_canon.get($getVar('unit.unit_type.' + $name, ''), '')
#if $_pressure
    #set $_unit = 'mbar'
#end if
#set $_band = $_deadbands.get($_unit, 0.5)
## current reading and the oldest reading in the last $_hours hours
#set $_curvh  = $getattr($current, $name)
#set $_binder = $getattr($span($hour_delta=$_hours), $name)
#set $_oldvh  = $_binder.first
## canonical-unit delta (decision) and display-unit delta (tooltip)
#set $_tv = None
#set $_disp = None
#try
    #if $_unit
        #set $_tv = $getattr($_curvh, $_unit).raw - $getattr($_oldvh, $_unit).raw
    #else
        #set $_tv = $_curvh.raw - $_oldvh.raw
    #end if
    #set $_disp = $_curvh.raw - $_oldvh.raw
#except
    #set $_tv = None
#end try
#if $_tv is not None
    #set $_lbl    = $getVar('unit.label.' + $name, '')
    #set $_disp_r = round($_disp, 2)
    #if $_pressure
        #set $_scale = float($_hours) / 3.0
        #if $_scale <= 0
            #set $_scale = 1.0
        #end if
        #set $_mag = abs($_tv)
        #if $_mag < 0.25 * $_scale
            ## steady
            <i class="wi wi-direction-right" title="$gettext('trend'): $_disp_r$_lbl ($_hours h)" data-toggle="tooltip" data-html="true"></i>
        #else
            #set $_dir = 'up' if $_tv > 0 else 'down'
            #set $_double = False
            #if $_mag >= 6.0 * $_scale
                ## very rapidly: two straight arrows
                #set $_wic = 'wi-direction-' + $_dir
                #set $_double = True
                #set $_word = 'Rising very rapidly' if $_dir == 'up' else 'Falling very rapidly'
            #else if $_mag >= 3.6 * $_scale
                ## quickly: one straight arrow
                #set $_wic = 'wi-direction-' + $_dir
                #set $_word = 'Rising quickly' if $_dir == 'up' else 'Falling quickly'
            #else
                ## slowly / rising: one diagonal arrow
                #set $_wic = 'wi-direction-up-right' if $_dir == 'up' else 'wi-direction-down-right'
                #set $_word = 'Rising' if $_dir == 'up' else 'Falling'
            #end if
            #if $_double
                <span title="$_word: $_disp_r$_lbl ($_hours h)" data-toggle="tooltip" data-html="true"><i class="wi $_wic"></i><i class="wi $_wic"></i></span>
            #else
                <i class="wi $_wic" title="$_word: $_disp_r$_lbl ($_hours h)" data-toggle="tooltip" data-html="true"></i>
            #end if
        #end if
    #else
        #if $_tv > $_band
            <i class="wi wi-direction-up-right" title="$gettext('trend'): $_disp_r$_lbl ($_hours h)" data-toggle="tooltip" data-html="true"></i>
        #else if $_tv < -$_band
            <i class="wi wi-direction-down-right" title="$gettext('trend'): $_disp_r$_lbl ($_hours h)" data-toggle="tooltip" data-html="true"></i>
        #else
            <i class="wi wi-direction-right" title="$gettext('trend'): $_disp_r$_lbl ($_hours h)" data-toggle="tooltip" data-html="true"></i>
        #end if
    #end if
#end if
