#encoding UTF-8
## +-------------------------------------------------------------------------+
## |    graph_bar_config.inc             JS config for default bar charts    |
## +-------------------------------------------------------------------------+

chart: {
    type: 'bar'
},
fill: {
    opacity: 0.1
},
xaxis: {
    type: 'datetime',
    hideOverlappingLabels: true,
    tickAmount: 8,
    labels: {
        formatter: function(val, timestamp) {
            #if $page == 'day'
                var fmt = "$Extras.Formatting.datetime_graph_label_day";
            #else if $page == 'week'
                var fmt = "$Extras.Formatting.datetime_graph_label_week";
            #else if $page == 'month'
                var fmt = "$Extras.Formatting.datetime_graph_label_month";
            #else if $page == 'year'
                var fmt = "$Extras.Formatting.datetime_graph_label_year";
            #else
                var fmt = "$Extras.Formatting.datetime_graph_label";
            #end if
            // If the format uses uppercase MM for minutes (common mistake), convert
            // only occurrences of ":MM" to Moment's minutes token ":mm" so we don't
            // change months (MM) to minutes.
            fmt = fmt.replace(/:MM/g, ':mm');
            return moment.unix(timestamp).format(fmt);
        }
    }
},
tooltip: {
    x: {
        formatter: function(val) {
            #if $page == 'day'
                var fmt = "$Extras.Formatting.datetime_graph_tooltip_day";
            #else if $page == 'week'
                var fmt = "$Extras.Formatting.datetime_graph_tooltip_week";
            #else if $page == 'month'
                var fmt = "$Extras.Formatting.datetime_graph_tooltip_month";
            #else if $page == 'year'
                var fmt = "$Extras.Formatting.datetime_graph_tooltip_year";
            #else
                var fmt = "$Extras.Formatting.datetime_graph_tooltip";
            #end if
            // convert minute token if needed (':MM' -> ':mm')
            fmt = fmt.replace(/:MM/g, ':mm');
            return moment.unix(val).format(fmt);
        }
    }
},
