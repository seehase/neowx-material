#encoding UTF-8
## ---------------------------------------------------------------------------
## Emit min / max / tickAmount for a day-aligned datetime x-axis so ticks land
## on whole-day (midnight) boundaries. Set before including (as #set global):
##   $align_start - first boundary, a midnight, in epoch SECONDS
##   $align_stop  - end reference in epoch seconds (e.g. $current.dateTime.raw)
##   $align_count - desired approx number of ticks; 0 = one tick per day
##   $align_mode  - 'midnight' or 'noon' (informational; for noon the caller
##                  passes align_start already shifted -12h so ticks land at noon)
## Inputs are seconds; min/max are emitted in MILLISECONDS to match the chart
## data ([$record.start.raw * 1000, ...]). Ticks are spaced a whole number of
## days apart, so a given count is approximate (rounded to a whole-day stride).
## ---------------------------------------------------------------------------
#set $_start = int($align_start)
#set $_total = int((int($align_stop) - $_start + 86399) // 86400)
#if $_total < 1
    #set $_total = 1
#end if
#set $_count = int($align_count)
#if $_count < 1
    #set $_count = $_total
#end if
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
