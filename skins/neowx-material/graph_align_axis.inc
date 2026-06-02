#encoding UTF-8
## ---------------------------------------------------------------------------
## Emit min / max / tickAmount for a day-aligned datetime x-axis so ticks land
## on whole-day (midnight) boundaries. Set before including (as #set global):
##   $align_start - first boundary, a midnight, in epoch SECONDS (matches data)
##   $align_stop  - end reference in epoch seconds (e.g. $current.dateTime.raw)
##   $align_count - desired approx number of ticks; 0 = one tick per day
##   $align_mode  - reserved ('midnight'); noon support TBD
## Ticks are spaced a whole number of days apart, so when a count is given it is
## approximate (rounded to the nearest whole-day stride to stay on midnight).
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
#set $_max = $_start + $_ticks * $_stride * 86400
    min: $_start,
    max: $_max,
    tickAmount: $_ticks,
