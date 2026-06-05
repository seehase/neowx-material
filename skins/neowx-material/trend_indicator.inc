#encoding UTF-8
## ---------------------------------------------------------------------------
## Trend indicator for observation $name (the "current" page).
## A Cheetah #include has its own scope and cannot see the caller's local
## $name, so the caller passes it via the $_trend_obs global. The caller only
## guarantees $name is in show_trend_on.
##
## We compute the change OURSELVES rather than use WeeWX $trend: $trend returns
## None unless an archive record lands within a small grace window of exactly
## (now - time_delta), which fails intermittently on coarser archive intervals.
## Here we use (current reading) - (oldest reading in the last N hours), which
## has a value whenever there is any recent data.
##
## The direction decision is made in a canonical unit per observation
## (barometer->hPa, temp->degC, ET->mm) so arrows behave the same in metric and
## imperial. Pressure uses the WMO/NWS 3-hour tendency categories shown with MDI
## single/double/triple chevrons; everything else uses a simple up/steady/down
## arrow with a per-observation dead-band. The tooltip shows the change in the
## user's display units.
##
## A debug HTML comment (<!-- nwm-trend ... -->) is emitted for every card so
## you can see the current/old values and the timestamp the "old" reading came
## from. Remove it once verified.
## ---------------------------------------------------------------------------
#set $name = $_trend_obs
#set $_hours = 3
#set $_pressure = $name in ('barometer', 'pressure', 'altimeter')
#set $_bands = {'outTemp': ['degree_C', 0.5], 'inTemp': ['degree_C', 0.5], 'ET': ['mm', 0.02]}
#set $_cfg  = $_bands.get($name, ['', 0.5])
#set $_unit = 'mbar' if $_pressure else $_cfg[0]
#set $_band = $_cfg[1]
## Current reading, and the oldest reading in the last $_hours hours.
#set $_curvh   = $getattr($current, $name)
#set $_binder  = $getattr($span($hour_delta=$_hours), $name)
#set $_oldvh   = $_binder.first
#set $_oldtime = $_binder.firsttime
## Canonical-unit delta (decision) and display-unit delta (tooltip).
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
<!-- nwm-trend obs="$name" unit="$_unit" now="$_curvh" now_time="$current.dateTime" old="$_oldvh" old_time="$_oldtime" canon_delta="$_tv" disp_delta="$_disp" -->
#if $_tv is not None
    #set $_lbl    = $getVar('unit.label.' + $name, '')
    #set $_disp_r = round($_disp, 2)
    #if $_pressure
        #set $_scale = float($_hours) / 3.0
        #if $_scale <= 0
            #set $_scale = 1.0
        #end if
        #set $_mag = abs($_tv)
        #if $_mag < 0.1 * $_scale
            <i class="wi wi-direction-right" title="$gettext('trend'): $_disp_r$_lbl ($_hours h)" data-toggle="tooltip" data-html="true"></i>
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
            <i class="mdi $_chev" title="$_word: $_disp_r$_lbl ($_hours h)" data-toggle="tooltip" data-html="true"></i>
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
