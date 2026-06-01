#encoding UTF-8
## +-----------------------------------------------------------------------------------+
## |    graph_line_config.inc             JS config for default line charts    |
## +-----------------------------------------------------------------------------------+

#set $allowMouseWheelZoom = "false"
#if $Extras.Appearance.get('allowMouseWheelZoom') == "true"
    #set $allowMouseWheelZoom = "true"
#end if

#set $defaultChartBehavior = "zoom"
#if $Extras.Appearance.get('defaultChartBehavior') == "pan"
    #set $defaultChartBehavior = "pan"
#end if

chart: {
    type: 'line',
    zoom: {
        enabled: false,
        type: 'x',
        autoScaleYaxis: false,
        allowMouseWheelZoom: $allowMouseWheelZoom,
    },
    toolbar: {
        autoSelected: '$defaultChartBehavior',
        export: {
            csv: {
                headerCategory: 'DateTime',
                dateFormatter(timestamp) {
                    return moment.unix(timestamp).toISOString()
                }
            }
        }
    },
},

dataLabels: {
    enabled: false
},

stroke: {
    width: 0,
},

plotOptions: {
    line: {
        borderRadius: 2,
    }
},

fill: {
    opacity: 0.7
},

markers: {
    size: 4,
    strokeWidth: 1,
    strokeOpacity: 0.5,
    strokeDashArray: 0,
    fillOpacity: 0.7,
    shape: "circle",
    radius: 1,
},

xaxis: {
    type: 'datetime',
    tickAmount: 8,
    trim: true,
    labels: {
        hideOverlappingLabels: true,
        tickAmount: 8,
        rotateAlways: false,
        hideOverlappingLabels: true,
        showDuplicates: false,
        trim: true,
        formatter: function(val, timestamp) {
            ## per-page key for $page (datetime_graph_label_<page>), else the base key
            #set $_lblval = $Extras.Formatting.get('datetime_graph_label_' + $page, $Extras.Formatting.get('datetime_graph_label', ''))
            #set $_lblval = ', '.join($_lblval) if isinstance($_lblval, list) else $_lblval
            ## resolve as a named [[Formatting]] constant; if not a known name, use the value literally
            #set $_lblfmt = $Extras.Formatting.get($_lblval, $_lblval)
            #set $_lblfmt = ', '.join($_lblfmt) if isinstance($_lblfmt, list) else $_lblfmt
            var fmt = "$_lblfmt";
            // If the format uses uppercase MM for minutes (common mistake), convert
            // only occurrences of ":MM" to Moment's minutes token ":mm" so we don't
            // change months (MM) to minutes.
            fmt = fmt.replace(/:MM/g, ':mm');
            return moment.unix(timestamp).format(fmt);
        }
    }
},

grid: {
    show: true,
    strokeDashArray: 0,
    position: 'back',
    xaxis: {
        lines: {
            show: true
        }
    },
    yaxis: {
        lines: {
            show: true
        }
    },
},

tooltip: {
    x: {
        formatter: function(val) {
            ## per-page key for $page (datetime_graph_tooltip_<page>), else the base key
            #set $_tipval = $Extras.Formatting.get('datetime_graph_tooltip_' + $page, $Extras.Formatting.get('datetime_graph_tooltip', ''))
            #set $_tipval = ', '.join($_tipval) if isinstance($_tipval, list) else $_tipval
            ## resolve as a named [[Formatting]] constant; if not a known name, use the value literally
            #set $_tipfmt = $Extras.Formatting.get($_tipval, $_tipval)
            #set $_tipfmt = ', '.join($_tipfmt) if isinstance($_tipfmt, list) else $_tipfmt
            var fmt = "$_tipfmt";
            fmt = fmt.replace(/:MM/g, ':mm');
            return moment.unix(val).format(fmt);
        }
    }
},
