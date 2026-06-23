#encoding UTF-8
## +-------------------------------------------------------------------------+
## | chart_hidden_series.inc   Collapse series named in $cc_hidden_names on  |
## | initial render (the "hideinitialvalues" feature) and reveal the chart   |
## | container the caller hid with opacity:0 to avoid a load-in flash.       |
## |                                                                         |
## | Expects in scope: $cc_hidden_names (list of exact ApexCharts series     |
## | names), $cc_type (graph config suffix), $cc_id (container element id).  |
## | Emits a merged chart.events.mounted handler, or nothing when no series  |
## | are hidden. Merge (not replace) so chart.type and any existing events   |
## | from graph_${cc_type}_config survive.                                   |
## +-------------------------------------------------------------------------+
#if len($cc_hidden_names) > 0
chart: {
    ...graph_${cc_type}_config.chart,
    events: {
        ...(graph_${cc_type}_config.chart && graph_${cc_type}_config.chart.events),
        mounted: function (chartContext) {
            try {
                #for $hn in $cc_hidden_names
                chartContext.hideSeries("$hn");
                #end for
            } finally {
                var _el = document.querySelector('#$cc_id');
                if (_el) { _el.style.opacity = '1'; }
            }
        }
    }
},
#end if
