#encoding UTF-8
## ---------------------------------------------------------------------------
## Emit `tickAmount: N,` for the datetime x-axis when a numeric tick count is
## configured for this page; emit nothing for "auto" (the default) so that
## ApexCharts places ticks on natural day / round boundaries.
## Resolution (keys live in [[Charts]]):
##     tick_amount_<page>  ->  tick_amount  ->  auto
## $page is one of: day (index + yesterday), week, month, year, telemetry.
## A fixed count is spaced evenly across the range, so ticks may not land on
## midnight; use "auto" when you want day-aligned ticks.
## ---------------------------------------------------------------------------
#set $_ta = $Extras.Charts.get('tick_amount_' + $page, $Extras.Charts.get('tick_amount', 'auto'))
#if $_ta and not isinstance($_ta, list) and $_ta.strip().isdigit() and int($_ta) > 0
    tickAmount: $int($_ta),
#end if
