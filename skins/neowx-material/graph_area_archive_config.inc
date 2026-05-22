#encoding UTF-8
## +-------------------------------------------------------------------------+
## |    graph_area_archive_config.inc   JS config for area charts in archive |
## +-------------------------------------------------------------------------+

chart: {
    type: 'area'
},
fill: {
    type: 'gradient',
    gradient: {
        shadeIntensity: 1,
        inverseColors: false,
        opacityFrom: 0.6,
        opacityTo: 0,
        stops: [0, 75, 100]
    },
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
