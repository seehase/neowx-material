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
            var fmt = "$Extras.Formatting.datetime_graph_label";
            fmt = fmt.replace(/:MM/g, ':mm');
            return moment.unix(timestamp).format(fmt);
        }
    }
},
tooltip: {
    x: {
        formatter: function(val) {
            var fmt = "$Extras.Formatting.datetime_graph_tooltip";
            fmt = fmt.replace(/:MM/g, ':mm');
            return moment.unix(val).format(fmt);
        }
    }
},
