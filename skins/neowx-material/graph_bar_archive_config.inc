#encoding UTF-8
## +-------------------------------------------------------------------------+
## |    graph_bar_archive_config.inc    JS config for bar charts in archive  |
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
            var fmt = "$Extras.Formatting.datetime_graph_archive";
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
