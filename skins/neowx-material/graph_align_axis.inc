#encoding UTF-8
## ---------------------------------------------------------------------------
## Emit min / max / tickAmount for an aligned datetime x-axis. Set before
## including (as #set global, epoch SECONDS):
##   $align_start - range start
##   $align_stop  - range end (e.g. $current.dateTime.raw, or period end)
##   $align_count - desired tick count; 0 = auto (~<=12 ticks)
## Granularity is chosen automatically from the span:
##   span <= 2 days  -> hour-aligned: ticks snapped to the top of the hour
##                      (e.g. 14:00) - i.e. the day page and telemetry
##   span <= 62 days -> day-aligned: ticks snapped to midnight (a whole-day
##                      stride, so they line up with the daily bars) - i.e.
##                      week and month
##   span >  62 days -> long range: ticks evenly spaced across [start, stop]
##                      (~monthly on a year), last tick on the end
## min / max are emitted in MILLISECONDS to match the chart data.
## ---------------------------------------------------------------------------
#set $_start = int($align_start)
#set $_stop  = int($align_stop)
#set $_secs  = $_stop - $_start
#if $_secs < 3600
    #set $_secs = 3600
#end if
#set $_count = int($align_count)
#if $_count < 1
    #set $_count = 12
#end if
#set $_total = int(($_secs + 86399) // 86400)
#if $_total < 1
    #set $_total = 1
#end if
#if $_secs <= 172800
    ## hour-aligned: whole-hour stride so ticks land on the hour (e.g. 14:00)
    #set $_hours = int(($_secs + 3599) // 3600)
    #set $_stride = int(round(float($_hours) / $_count))
    #if $_stride < 1
        #set $_stride = 1
    #end if
    #set $_ticks = int(($_hours + $_stride - 1) // $_stride)
    #set $_h0 = int(($_start // 3600) * 3600)
    #set $_min_ms = $_h0 * 1000
    #set $_max_ms = ($_h0 + $_ticks * $_stride * 3600) * 1000
    min: $_min_ms,
    max: $_max_ms,
    tickAmount: $_ticks,
#else if $_total <= 62
    ## day-aligned: whole-day stride so ticks land on midnight
    #set $_stride = int(round(float($_total) / $_count))
    #if $_stride < 1
        #set $_stride = 1
    #end if
    #set $_ticks = int(($_total + $_stride - 1) // $_stride)
    #set $_min_ms = $_start * 1000
    #set $_max_ms = ($_start + $_ticks * $_stride * 86400) * 1000
    min: $_min_ms,
    max: $_max_ms,
    tickAmount: $_ticks,
#else
    ## long span: ticks evenly spaced across the range (~monthly)
    #set $_min_ms = $_start * 1000
    #set $_max_ms = $_stop * 1000
    min: $_min_ms,
    max: $_max_ms,
    tickAmount: $_count,
#end if
