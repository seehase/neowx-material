#encoding UTF-8
## ---------------------------------------------------------------------------
## Resolve a custom chart's optional per-chart tick_amount override into
## chart-scoped globals. Include from the customChart* loop AFTER setting
## (as #set global):
##   $cc_name  - the customChart* key (e.g. customChartOutTemp)
##   $cc_scope - page scope key: week / month / year (etc.)
## The value (page subsection -> top-level) accepts the same forms as the
## [[Charts]] tick_amount keys: auto / fixed:N (or N) / align / align:N.
## When the chart sets nothing, $cc_tick_set stays False and the page setting
## ($pg_align_mid / the inherited graph_tick_amount.inc) is used unchanged.
## Outputs (globals), consumed by chart_tick_axis.inc:
##   $cc_tick_set   - True when the chart specified its own tick_amount
##   $cc_tick_align - True for align / align:N
##   $cc_tick_count - N from align:N (0 = auto count, ~<=12)
##   $cc_tick_fixed - N from fixed:N / N (0 = none)
## ---------------------------------------------------------------------------
#set global $cc_tick_set   = False
#set global $cc_tick_align = False
#set global $cc_tick_count = 0
#set global $cc_tick_fixed = 0
#set $_cc   = $Extras.Appearance.get($cc_name, {})
#set $_page = $_cc.get($cc_scope, {})
#set $_spec = $_page.get('tick_amount', $_cc.get('tick_amount', ''))
#if isinstance($_spec, list)
    #set $_spec = $_spec[0] if $_spec else ''
#end if
#set $_spec = str($_spec).strip().lower() if $_spec else ''
#if $_spec
    #set global $cc_tick_set = True
    #set $_parts = $_spec.split(':')
    #if $_parts[0] == 'align'
        #set global $cc_tick_align = True
        #set global $cc_tick_count = int($_parts[1]) if (len($_parts) >= 2 and $_parts[1].strip().isdigit()) else 0
    #else if $_parts[0] == 'fixed'
        #set global $cc_tick_fixed = int($_parts[1]) if (len($_parts) >= 2 and $_parts[1].strip().isdigit()) else 0
    #else if $_spec.isdigit()
        #set global $cc_tick_fixed = int($_spec)
    #end if
    ## anything else (e.g. 'auto') leaves align False / fixed 0 -> ticks auto
#end if
