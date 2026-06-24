#encoding UTF-8
## +-------------------------------------------------------------------------+
## | chart_hidden_series.inc   Collapse series named in $cc_hidden_names on  |
## | initial render (the "hidevalues" feature) and reveal the chart   |
## | container the caller hid with opacity:0 to avoid a load-in flash.       |
## |                                                                         |
## | Cheetah #include runs in a scope that only sees GLOBALS (not the        |
## | caller's local #set vars), so the caller MUST set $cc_hidden_names with  |
## | "#set global". The chart type and container id are derived here from     |
## | the already-global $cc_name (the customChart* key) so callers don't      |
## | have to globalize their local $cc_type / $cc_id too.                     |
## |                                                                         |
## | Emits a merged chart.events.mounted handler, or nothing when no series   |
## | are hidden. Merge (not replace) so chart.type and any existing events    |
## | from graph_<type>_config survive.                                        |
## +-------------------------------------------------------------------------+
#if len($cc_hidden_names) > 0
#set $_hs_type = $Extras.Appearance.get($cc_name, {}).get('charttype', 'area')
#set $_hs_id   = $cc_name + 'chart'
chart: {
    ...graph_${_hs_type}_config.chart,
    events: {
        ...(graph_${_hs_type}_config.chart && graph_${_hs_type}_config.chart.events),
        mounted: function (chartContext) {
            try {
                #for $hn in $cc_hidden_names
                chartContext.hideSeries("$hn");
                #end for
            } finally {
                var _el = document.querySelector('#$_hs_id');
                if (_el) { _el.style.opacity = '1'; }
            }
        }
    }
},
#end if
